"""
Business Logic Services for Project Tehama API
"""
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import Position, PortfolioSummary, Alert, Recommendation
from api.cache_manager import cache_manager

# Import risk management agents
try:
    from agents.risk_committee import get_risk_committee
    from agents.meta_agent import get_meta_agent
    RISK_AGENTS_AVAILABLE = True
except ImportError:
    RISK_AGENTS_AVAILABLE = False
    print("Warning: Risk management agents not available")

# Import analyst team
try:
    from agents.technical_agent import get_technical_agent
    from agents.fundamental_agent import get_fundamental_agent
    from agents.sentiment_agent import get_sentiment_agent
    from agents.risk_agent import get_risk_agent
    ANALYST_TEAM_AVAILABLE = True
except ImportError:
    ANALYST_TEAM_AVAILABLE = False
    print("Warning: Analyst team not available")

# Import existing modules
try:
    from config import Config
    import alpaca_trade_api as tradeapi

    # Determine if using paper trading based on URL
    IS_PAPER = 'paper' in (Config.ALPACA_BASE_URL or '').lower()

    ALPACA_AVAILABLE = True
    print(f"Alpaca client imported successfully (Paper mode: {IS_PAPER})")
    print(f"  API Key: {Config.ALPACA_API_KEY[:8]}..." if Config.ALPACA_API_KEY else "  API Key: NOT SET")
except ImportError as e:
    ALPACA_AVAILABLE = False
    Config = None
    IS_PAPER = True
    tradeapi = None
    print(f"Warning: Alpaca client not available - {e}")
    print("  Make sure config.py exists and alpaca-trade-api is installed")
except Exception as e:
    ALPACA_AVAILABLE = False
    Config = None
    IS_PAPER = True
    tradeapi = None
    print(f"Warning: Error importing Alpaca - {e}")


class PortfolioService:
    """Service for portfolio data"""

    def __init__(self):
        self.api = None
        if ALPACA_AVAILABLE and Config and tradeapi:
            try:
                self.api = tradeapi.REST(
                    Config.ALPACA_API_KEY,
                    Config.ALPACA_SECRET_KEY,
                    Config.ALPACA_BASE_URL,
                    api_version='v2'
                )
                print(f"Alpaca REST API initialized successfully")
            except Exception as e:
                print(f"ERROR: Could not initialize Alpaca client: {e}")

    def _fetch_portfolio_from_alpaca(self) -> dict:
        """Internal method to fetch portfolio from Alpaca (for caching)"""
        if not self.api:
            raise Exception("Alpaca API not initialized")

        print("Fetching portfolio from Alpaca...")
        # Get account info
        account = self.api.get_account()
        print(f"  Account value: ${float(account.portfolio_value):.2f}")

        # Get all positions
        positions = self.api.list_positions()
        print(f"  Total positions from Alpaca: {len(positions)}")

        position_list = []
        for pos in positions:
            current_price = float(pos.current_price)
            avg_price = float(pos.avg_entry_price)
            qty = float(pos.qty)
            market_value = float(pos.market_value)
            unrealized_plpc = float(pos.unrealized_plpc) * 100
            change_today = float(pos.change_today) * 100

            print(f"    - {pos.symbol}: {qty} shares @ ${current_price:.2f} (P/L: {unrealized_plpc:+.2f}%)")

            position_list.append({
                'ticker': pos.symbol,
                'qty': qty,
                'avg_entry_price': avg_price,
                'current_price': current_price,
                'market_value': market_value,
                'unrealized_plpc': unrealized_plpc,
                'daily_change_pct': change_today
            })

        print(f"Successfully fetched {len(position_list)} positions")

        last_equity = float(account.last_equity)
        portfolio_value = float(account.portfolio_value)
        daily_change = portfolio_value - last_equity
        daily_change_pct = (daily_change / last_equity * 100) if last_equity > 0 else 0

        return {
            'total_value': portfolio_value,
            'cash': float(account.cash),
            'daily_change': daily_change,
            'daily_change_pct': daily_change_pct,
            'positions': position_list
        }

    async def get_portfolio_summary(self) -> PortfolioSummary:
        """Get current portfolio summary with intelligent caching"""
        if not self.api:
            print("WARNING: Using MOCK data - Alpaca client not initialized")
            # Return mock data if Alpaca not available
            return PortfolioSummary(
                total_value=939.49,
                cash=0.0,
                daily_change=39.64,
                daily_change_pct=4.41,
                positions=[
                    Position(
                        ticker="APLD",
                        qty=5.0,
                        avg_entry_price=30.70,
                        current_price=36.28,
                        market_value=181.40,
                        unrealized_plpc=18.17,
                        daily_change_pct=5.2
                    ),
                    Position(
                        ticker="NTLA",
                        qty=4.0,
                        avg_entry_price=22.50,
                        current_price=28.60,
                        market_value=114.40,
                        unrealized_plpc=27.11,
                        daily_change_pct=8.3
                    )
                ]
            )

        try:
            # Use cache with intelligent TTL
            portfolio_data = await cache_manager.get_or_fetch(
                key="portfolio_summary",
                fetch_function=self._fetch_portfolio_from_alpaca
            )

            # Convert dict to Pydantic models
            positions = [Position(**pos) for pos in portfolio_data['positions']]

            return PortfolioSummary(
                total_value=portfolio_data['total_value'],
                cash=portfolio_data['cash'],
                daily_change=portfolio_data['daily_change'],
                daily_change_pct=portfolio_data['daily_change_pct'],
                positions=positions
            )
        except Exception as e:
            print(f"ERROR fetching portfolio: {e}")
            import traceback
            traceback.print_exc()
            raise


class AlertService:
    """Service for alerts and notifications"""

    def __init__(self):
        self.alerts: List[Alert] = []
        self._generate_sample_alerts()

    def _generate_sample_alerts(self):
        """Generate sample alerts for testing"""
        self.alerts = [
            Alert(
                type="price_alert",
                ticker="APLD",
                message="APLD broke above $36 resistance - momentum continuation signal",
                severity="info",
                timestamp=datetime.now()
            ),
            Alert(
                type="news_alert",
                ticker="NTLA",
                message="NTLA positive gene editing breakthrough announced - catalyst detected",
                severity="info",
                timestamp=datetime.now()
            ),
            Alert(
                type="technical_alert",
                ticker="UUUU",
                message="UUUU oversold on RSI (28) - potential reversal setup",
                severity="warning",
                timestamp=datetime.now()
            )
        ]

    def _fetch_alerts(self, limit: int = 10) -> List[dict]:
        """Internal method to fetch alerts (for caching)"""
        # Convert alerts to dict for JSON serialization
        return [
            {
                'type': alert.type,
                'ticker': alert.ticker,
                'message': alert.message,
                'severity': alert.severity,
                'timestamp': alert.timestamp.isoformat()
            }
            for alert in self.alerts[:limit]
        ]

    async def get_recent_alerts(self, limit: int = 10, use_cache: bool = True) -> List[Alert]:
        """Get recent alerts with intelligent caching"""
        if not use_cache:
            print("Cache bypassed for alerts")
            return self.alerts[:limit]

        try:
            # Use intelligent caching
            alerts_data = await cache_manager.get_or_fetch(
                key=f"alerts_limit_{limit}",
                fetch_function=lambda: self._fetch_alerts(limit)
            )

            # Convert dict back to Pydantic models
            return [
                Alert(
                    type=alert['type'],
                    ticker=alert.get('ticker'),
                    message=alert['message'],
                    severity=alert['severity'],
                    timestamp=datetime.fromisoformat(alert['timestamp'])
                )
                for alert in alerts_data
            ]
        except Exception as e:
            print(f"ERROR fetching alerts: {e}")
            # Fallback to non-cached
            return self.alerts[:limit]


class RecommendationService:
    """Service for AI recommendations"""

    def __init__(self):
        self.recommendations: List[Recommendation] = []
        self._generate_sample_recommendations()

        # Initialize risk management agents
        if RISK_AGENTS_AVAILABLE:
            self.risk_committee = get_risk_committee()
            self.meta_agent = get_meta_agent()
        else:
            self.risk_committee = None
            self.meta_agent = None

        # Initialize analyst team
        if ANALYST_TEAM_AVAILABLE:
            self.technical_agent = get_technical_agent()
            self.fundamental_agent = get_fundamental_agent()
            self.sentiment_agent = get_sentiment_agent()
            self.risk_agent = get_risk_agent()
            print("Analyst team initialized (Technical, Fundamental, Sentiment, Risk)")
        else:
            self.technical_agent = None
            self.fundamental_agent = None
            self.sentiment_agent = None
            self.risk_agent = None

    def _generate_sample_recommendations(self):
        """Generate sample recommendations for testing"""
        self.recommendations = [
            Recommendation(
                id="rec_001",
                ticker="APLD",
                action="HOLD",
                qty=None,
                target_price=40.00,
                reasoning="Strong momentum with positive catalyst sentiment. In bullish market regime with 18% unrealized gains. Set trailing stop at $32.",
                confidence=0.85,
                agents=["momentum_agent", "sentiment_agent", "regime_agent"],
                status="pending"
            ),
            Recommendation(
                id="rec_002",
                ticker="NTLA",
                action="ADD",
                qty=2.0,
                target_price=25.00,
                reasoning="Biotech momentum play with perfect positive sentiment (1.00 score). Add on pullback to $25-26 support zone.",
                confidence=0.78,
                agents=["biotech_agent", "catalyst_agent"],
                status="pending"
            ),
            Recommendation(
                id="rec_003",
                ticker="UUUU",
                action="ADD",
                qty=3.0,
                target_price=22.00,
                reasoning="Uranium pullback with positive news sentiment. Add at $22-22.50 range with stop at $18.50.",
                confidence=0.72,
                agents=["contrarian_agent", "sector_agent"],
                status="pending"
            )
        ]

    def _fetch_recommendations(self, status: str = None) -> List[dict]:
        """Internal method to fetch recommendations (for caching)"""
        recs = self.recommendations
        if status:
            recs = [r for r in recs if r.status == status]

        # Convert to dict for JSON serialization
        return [
            {
                'id': rec.id,
                'ticker': rec.ticker,
                'action': rec.action,
                'qty': rec.qty,
                'target_price': rec.target_price,
                'reasoning': rec.reasoning,
                'confidence': rec.confidence,
                'agents': rec.agents,
                'status': rec.status,
                'created_at': rec.created_at.isoformat()
            }
            for rec in recs
        ]

    def _apply_risk_committee(self, recommendation: Recommendation, portfolio_context: Dict = None) -> Dict:
        """
        Apply Risk Committee debate to recommendation.

        Args:
            recommendation: Base recommendation
            portfolio_context: Current portfolio state

        Returns:
            Risk-adjusted recommendation data
        """
        if not self.risk_committee or recommendation.action in ["HOLD"]:
            # No risk adjustment needed for HOLD
            return None

        # Convert to dict for risk committee
        rec_dict = {
            "ticker": recommendation.ticker,
            "action": recommendation.action,
            "qty": recommendation.qty or 5,  # Default if not set
            "target_price": recommendation.target_price or 0,
            "reasoning": recommendation.reasoning,
            "confidence": recommendation.confidence
        }

        # Run through Risk Committee
        try:
            result = self.risk_committee.debate_position_sizing(
                recommendation=rec_dict,
                portfolio_context=portfolio_context
            )

            return {
                "original_qty": recommendation.qty,
                "risk_adjusted_qty": result.get("proposals", {}).get("neutral", {}).get("proposed_qty"),
                "stop_loss": result.get("stop_loss"),
                "risk_debate_summary": result.get("reasoning"),
                "risk_winner": result.get("winner")
            }
        except Exception as e:
            print(f"Risk Committee error: {e}")
            return None

    def _generate_multi_agent_recommendation(self, ticker: str, portfolio_context: Dict = None) -> Optional[Recommendation]:
        """
        Generate recommendation using analyst team + Meta-Agent aggregation.

        Pipeline:
        1. Run 4 agents (Technical, Fundamental, Sentiment, Risk)
        2. Aggregate with Meta-Agent (applies diversity penalty)
        3. Return final recommendation

        Args:
            ticker: Stock ticker to analyze
            portfolio_context: Portfolio state for risk analysis

        Returns:
            Recommendation object with consensus action, confidence, reasoning
        """
        if not ANALYST_TEAM_AVAILABLE or not self.meta_agent:
            print(f"Analyst team or Meta-Agent not available for {ticker}")
            return None

        print(f"\n[RecommendationService] Generating multi-agent recommendation for {ticker}")

        # Run all 4 agents in parallel (conceptually)
        agent_recommendations = []

        try:
            # Technical analysis
            tech_result = self.technical_agent.analyze(ticker, portfolio_context)
            agent_recommendations.append(tech_result)
            print(f"  [Technical] {tech_result['action']} (confidence: {tech_result['confidence']}%)")
        except Exception as e:
            print(f"  [Technical] Error: {e}")

        try:
            # Fundamental analysis
            fund_result = self.fundamental_agent.analyze(ticker, portfolio_context)
            agent_recommendations.append(fund_result)
            print(f"  [Fundamental] {fund_result['action']} (confidence: {fund_result['confidence']}%)")
        except Exception as e:
            print(f"  [Fundamental] Error: {e}")

        try:
            # Sentiment analysis
            sent_result = self.sentiment_agent.analyze(ticker, portfolio_context)
            agent_recommendations.append(sent_result)
            print(f"  [Sentiment] {sent_result['action']} (confidence: {sent_result['confidence']}%)")
        except Exception as e:
            print(f"  [Sentiment] Error: {e}")

        try:
            # Risk analysis
            risk_result = self.risk_agent.analyze(ticker, portfolio_context)
            agent_recommendations.append(risk_result)
            print(f"  [Risk] {risk_result['action']} (confidence: {risk_result['confidence']}%)")
        except Exception as e:
            print(f"  [Risk] Error: {e}")

        if not agent_recommendations:
            print(f"  No agent recommendations generated for {ticker}")
            return None

        # Aggregate with Meta-Agent
        try:
            meta_result = self.meta_agent.aggregate_recommendations(agent_recommendations, portfolio_context)

            print(f"  [Meta-Agent] Consensus: {meta_result['action']} (confidence: {meta_result['confidence']}%)")
            print(f"  [Meta-Agent] {meta_result.get('warning', '')}")

            # Build Recommendation object
            agent_names = [rec['agent'] for rec in agent_recommendations]

            recommendation = Recommendation(
                id=f"rec_{ticker}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                ticker=ticker,
                action=meta_result['action'],
                qty=None,  # Will be set by Risk Committee if apply_risk=true
                target_price=None,  # Could extract from technical analysis
                reasoning=meta_result.get('meta_analysis', ''),
                confidence=meta_result['confidence'] / 100,  # Convert to 0-1
                agents=agent_names,
                status="pending"
            )

            return recommendation

        except Exception as e:
            print(f"  [Meta-Agent] Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def get_recommendations(self, status: str = None, use_cache: bool = True, apply_risk: bool = False) -> List[Recommendation]:
        """
        Get recommendations with intelligent caching (5 min TTL)

        Args:
            status: Filter by status
            use_cache: Use cached results
            apply_risk: Apply Risk Committee to recommendations

        Returns:
            List of recommendations
        """
        if not use_cache:
            print("Cache bypassed for recommendations")
            if status:
                return [r for r in self.recommendations if r.status == status]
            return self.recommendations

        try:
            # Use 5-minute cache for recommendations
            cache_key = f"recommendations_status_{status or 'all'}"
            recs_data = await cache_manager.get_or_fetch(
                key=cache_key,
                fetch_function=lambda: self._fetch_recommendations(status),
                ttl_seconds=300  # 5 minutes
            )

            # Convert dict back to Pydantic models
            recommendations = [
                Recommendation(
                    id=rec['id'],
                    ticker=rec['ticker'],
                    action=rec['action'],
                    qty=rec.get('qty'),
                    target_price=rec.get('target_price'),
                    reasoning=rec['reasoning'],
                    confidence=rec['confidence'],
                    agents=rec['agents'],
                    status=rec['status'],
                    created_at=datetime.fromisoformat(rec['created_at'])
                )
                for rec in recs_data
            ]

            # Apply Risk Committee if requested
            if apply_risk and self.risk_committee:
                for rec in recommendations:
                    risk_result = self._apply_risk_committee(rec)
                    if risk_result:
                        # Add risk data to reasoning
                        rec.reasoning += f"\n\n[Risk Committee] {risk_result['risk_debate_summary']}"
                        rec.qty = risk_result['risk_adjusted_qty']

            return recommendations

        except Exception as e:
            print(f"ERROR fetching recommendations: {e}")
            # Fallback to non-cached
            if status:
                return [r for r in self.recommendations if r.status == status]
            return self.recommendations


class AgentService:
    """Service for AI agent status"""

    def _fetch_agent_status(self) -> Dict[str, Any]:
        """Internal method to fetch agent status (for caching)"""
        # Import scanner to get real stats
        try:
            from agents.opportunity_scanner import get_scanner
            scanner = get_scanner()
            scanner_stats = scanner.last_scan_stats
            print(f"[DEBUG] Scanner stats loaded: {bool(scanner_stats)}")
            print(f"[DEBUG] Scanner stats: {scanner_stats}")
        except Exception as e:
            print(f"Warning: Could not load scanner stats: {e}")
            import traceback
            traceback.print_exc()
            scanner_stats = {}

        agents_list = [
            {
                "name": "momentum_agent",
                "status": "active",
                "last_run": datetime.now().isoformat(),
                "positions_analyzed": 6,
                "recommendations_generated": 2
            },
            {
                "name": "sentiment_agent",
                "status": "active",
                "last_run": datetime.now().isoformat(),
                "news_articles_analyzed": 15,
                "sentiment_scores_generated": 6
            },
            {
                "name": "regime_agent",
                "status": "active",
                "last_run": datetime.now().isoformat(),
                "market_regime": "BULLISH",
                "confidence": 0.55
            },
            {
                "name": "contrarian_agent",
                "status": "active",
                "last_run": datetime.now().isoformat(),
                "dip_opportunities_found": 1
            },
            {
                "name": "catalyst_agent",
                "status": "active",
                "last_run": datetime.now().isoformat(),
                "catalysts_detected": 3
            }
        ]

        # Add opportunity scanner if stats available
        if scanner_stats:
            agents_list.append({
                "name": "opportunity_scanner",
                "status": "active",
                "last_run": scanner_stats.get("timestamp", "Never"),
                "tickers_scanned": scanner_stats.get("tickers_scanned", 0),
                "opportunities_found": scanner_stats.get("opportunities_found", 0),
                "scan_time": scanner_stats.get("scan_time", "N/A")
            })

        total_agents = len(agents_list)
        active_agents = len([a for a in agents_list if a["status"] == "active"])

        return {
            "agents": agents_list,
            "summary": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "inactive_agents": total_agents - active_agents,
                "system_health": "healthy"
            }
        }

    async def get_agent_status(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get status of all AI agents with 2-minute caching"""
        if not use_cache:
            print("Cache bypassed for agent status")
            return self._fetch_agent_status()

        try:
            # Use 2-minute cache for agent status
            agent_data = await cache_manager.get_or_fetch(
                key="agent_status",
                fetch_function=self._fetch_agent_status,
                ttl_seconds=120  # 2 minutes
            )
            return agent_data
        except Exception as e:
            print(f"ERROR fetching agent status: {e}")
            # Fallback to non-cached
            return self._fetch_agent_status()


# Singleton instances
portfolio_service = PortfolioService()
alert_service = AlertService()
recommendation_service = RecommendationService()
agent_service = AgentService()
