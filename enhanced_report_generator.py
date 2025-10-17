"""
Enhanced Report Generator using existing Project Tehama infrastructure
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import os
from anthropic import AsyncAnthropic


class EnhancedReportGenerator:
    def __init__(self, market_service, portfolio_service):
        """
        Initialize with YOUR EXISTING services
        """
        self.market = market_service  # Your existing market data service
        self.portfolio = portfolio_service  # Your existing portfolio tracker
        self.claude = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    async def generate_morning_brief(self) -> str:
        """
        Generate enhanced morning brief using YOUR data sources
        """

        # Gather data from YOUR EXISTING services
        portfolio_data = await self.portfolio.get_current_positions()

        # Use ALL your market data sources
        market_data = await asyncio.gather(
            self.market.get_spy_data(),  # Alpha Vantage
            self.market.get_futures(),  # Finnhub
            self.market.get_sector_performance(),  # FMP
            self.market.scan_unusual_activity(),  # Polygon
            self.market.get_comprehensive_news(portfolio_data['tickers']),  # News API
            self.market.get_insider_activity(portfolio_data['tickers'])  # SEC API
        )

        spy_data, futures, sectors, unusual, news, insiders = market_data

        # Analyze regime using your data
        regime = await self.market.analyze_market_regime()

        # Generate Claude analysis for each position
        position_analyses = {}
        for position in portfolio_data['positions']:
            ticker = position['symbol']

            # Aggregate ALL your data sources for this ticker
            ticker_context = {
                'fundamentals': await self.market.get_fundamentals_fmp(ticker),
                'technicals': await self.market.get_technicals_alpha_vantage(ticker),
                'news': news.get(ticker, {}),
                'insider_activity': insiders.get(ticker, {}),
                'options_flow': await self.market.get_options_flow_polygon(ticker)
            }

            # Get Claude's analysis
            analysis = await self._get_claude_analysis(position, ticker_context, regime)
            position_analyses[ticker] = analysis

        # Find opportunities using YOUR scanners
        opportunities = await self._scan_opportunities()

        # AGGRESSIVE TRADER FEATURE: Scan for contrarian dip-buy opportunities
        contrarian_opps = await self._scan_contrarian_opportunities(portfolio_data, regime)

        # Build the report
        report = f"""
# 📊 INTELLIGENT MORNING BRIEF - Project Tehama
**{datetime.now().strftime('%A, %B %d, %Y')}**
**Data Sources: Alpha Vantage | Finnhub | FMP | Polygon | SEC | News API**

## 🎯 EXECUTIVE SUMMARY
{await self._generate_executive_summary(portfolio_data, regime, opportunities)}

## 📈 MARKET INTELLIGENCE
### Multi-Source Regime Analysis
**Trend**: {regime['trend']} (Alpha Vantage SMA Analysis)
**Volatility**: {regime['volatility']} (Polygon VIX: {regime.get('volatility_value', 'N/A')})
**Breadth**: {regime['breadth']} (FMP Advance/Decline)
**Futures**: SPY {futures.get('ES', 0):+.2f}% | NQ {futures.get('NQ', 0):+.2f}% (Finnhub)

### Sector Performance (FMP)
{self._format_sector_performance(sectors)}

### Unusual Activity (Polygon)
{self._format_unusual_activity(unusual[:5])}

## 💼 PORTFOLIO ANALYSIS
**Total Value**: ${portfolio_data['total_value']:,.2f}
**Day P/L**: ${portfolio_data['day_pl']:+,.2f} ({portfolio_data['day_pl_pct']:+.2f}%)

### Position Intelligence
{self._format_position_analyses(position_analyses)}

### Insider Activity (SEC API)
{self._format_insider_activity(insiders)}

## 🎯 HIGH-PROBABILITY SETUPS
{await self._format_opportunities(opportunities)}

## 🔥 CONTRARIAN DIP-BUY OPPORTUNITIES (Aggressive Trader)
{self._format_contrarian_opportunities(contrarian_opps)}

## 📰 NEWS CATALYSTS (Multi-Source)
### Finnhub Institutional News
{self._format_finnhub_news(news)}

### News API Sentiment
{self._format_newsapi_sentiment(news)}

## ⚡ ACTION PLAN
{await self._generate_action_plan(portfolio_data, regime, opportunities)}

---
*Generated using: 6 data sources | {len(portfolio_data['positions'])} positions analyzed*
*Next update: After market open*
"""
        return report

    async def _get_claude_analysis(self, position: Dict, context: Dict, regime: Dict) -> str:
        """
        Get Claude's analysis using all your data sources with aggressive momentum trader personality
        """

        # SYSTEM PROMPT - Defines Claude's personality and approach
        system_prompt = """You are an aggressive microcap momentum trader with high risk tolerance. Your philosophy:

RISK APPETITE:
- Willing to accept -20% to -30% losses on individual positions for potential 5-10x winners
- Daily volatility of -5% to -10% is NORMAL and not a reason to sell
- Let winners run with trailing stops - don't cut flowers to water weeds
- Red days in bull markets = buying opportunities on quality names, not panic selling

WHEN TO SELL (be selective):
- Thesis fundamentally broken (company issues, not just price)
- Major technical breakdown with heavy volume (not normal pullback)
- Better opportunity requiring capital reallocation
- Position reaches predetermined stop loss (-20% to -25%)

WHEN TO ADD (be aggressive):
- Market strong but stock weak = dip buying opportunity
- Positive catalysts + temporary pullback = add to winners
- Strong thesis + technical oversold (RSI <30) = scale in
- Insider buying during weakness = high conviction add

ANALYSIS STYLE:
- Focus on WHY it's moving (catalyst, sector rotation, technical), not just THAT it's moving
- Distinguish between noise (intraday volatility) and signal (trend change)
- Always provide specific price levels for adds/trims/stops
- Emphasize opportunity cost of selling too early vs. protecting capital

CURRENT MARKET: If market regime is BULLISH and stock is down, default to "hold/add" unless clear fundamental deterioration."""

        # USER PROMPT - The specific analysis request
        user_prompt = f"""
Analyze this position using comprehensive market data:

POSITION: {position['symbol']} - {position['shares']} shares @ ${position['entry']:.2f}
Current: ${position['current']:.2f} ({position['pnl_pct']:+.2f}%)

FUNDAMENTALS (FMP):
- P/E: {context['fundamentals'].get('pe_ratio', 'N/A')}
- Revenue Growth: {context['fundamentals'].get('revenue_growth', 'N/A')}
- Insider Ownership: {context['fundamentals'].get('insider_ownership', 'N/A')}

TECHNICALS (Alpha Vantage):
- RSI: {context['technicals'].get('rsi', 'N/A')}
- MACD: {context['technicals'].get('macd', 'N/A')}
- Support: ${context['technicals'].get('support', 'N/A')}
- Resistance: ${context['technicals'].get('resistance', 'N/A')}

NEWS SENTIMENT (News API + Finnhub):
- Articles: {len(context['news'].get('articles', []))}
- Sentiment: {context['news'].get('sentiment', {}).get('label', 'Neutral')}
- Score: {context['news'].get('sentiment', {}).get('score', 0):.2f}
- Catalyst: {context['news'].get('catalyst_detected', False)}

INSIDER ACTIVITY (SEC):
- Recent Buys: {len(context['insider_activity'].get('recent_buys', []))}
- Recent Sells: {len(context['insider_activity'].get('recent_sells', []))}
- Net Signal: {context['insider_activity'].get('signal', 'Neutral')}

OPTIONS FLOW (Polygon):
- Unusual Activity: {context['options_flow'].get('unusual', False)}
- Put/Call Ratio: {context['options_flow'].get('put_call_ratio', 'N/A')}

MARKET REGIME: {regime['trend']} with {regime['volatility']} volatility, {regime['breadth']} breadth

Provide 2-3 sentence actionable analysis with specific price levels. Consider if this is a HOLD/ADD opportunity or genuine concern."""

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=250,  # Increased for more detailed aggressive analysis
            system=system_prompt,  # Add the aggressive momentum trader personality
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    async def _scan_opportunities(self) -> List[Dict]:
        """
        Use YOUR EXISTING scanners with all data sources
        """
        # Combine scans from all your sources
        opportunities = []

        # Polygon unusual volume scan
        polygon_unusual = await self.market.scan_unusual_activity()

        # FMP value scan (if you have this method)
        # fmp_value = await self.market.scan_value_stocks_fmp()

        # SEC insider buying scan (if you have this method)
        # sec_insiders = await self.market.scan_insider_buying_sec()

        # For now, use what's available
        all_opportunities = polygon_unusual

        # Score each opportunity using all data sources
        for opp in all_opportunities:
            opp['score'] = await self._score_opportunity(opp)

        # Return top 5
        return sorted(all_opportunities, key=lambda x: x['score'], reverse=True)[:5]

    async def _scan_contrarian_opportunities(self, portfolio_data: Dict, regime: Dict) -> List[Dict]:
        """
        Identify buying opportunities when market is strong but your stocks are weak.
        This is where the best entries happen - aggressive dip buying in bull markets!
        """
        if regime['trend'] != 'BULLISH':
            return []  # Only look for contrarian buys in bull markets

        opportunities = []

        for position in portfolio_data['positions']:
            ticker = position['symbol']
            current_price = position['current']
            entry_price = position['entry']
            pnl_pct = position['pnl_pct']

            # Calculate day change (approximate from current data)
            # If you have real-time day change, use that instead
            day_change = ((current_price - entry_price) / entry_price) * 100

            # Criteria: Market strong + Stock weak + Good fundamentals
            if day_change < -3 or pnl_pct < -5:  # Down 3%+ today OR down 5%+ overall
                try:
                    # Get context
                    news = await self.market.get_comprehensive_news([ticker])
                    ticker_news = news.get(ticker, {})
                    sentiment = ticker_news.get('sentiment', {})

                    insider = await self.market.get_insider_activity([ticker])
                    ticker_insider = insider.get(ticker, {})

                    technicals = await self.market.get_technicals_alpha_vantage(ticker)
                    rsi = technicals.get('rsi')

                    # BUYING SIGNAL: Down on no bad news + oversold + no insider selling
                    is_oversold = rsi and rsi < 35
                    no_bad_news = sentiment.get('label') != 'NEGATIVE'
                    no_insider_selling = ticker_insider.get('signal') != 'BEARISH'
                    has_positive_catalyst = ticker_news.get('catalyst_detected', False)

                    if is_oversold and no_bad_news and no_insider_selling:
                        support_level = current_price * 0.97  # 3% below current
                        add_level = current_price * 0.95      # 5% below current (better entry)

                        opportunities.append({
                            'ticker': ticker,
                            'type': 'DIP_BUY',
                            'current_price': current_price,
                            'day_change': day_change,
                            'pnl_pct': pnl_pct,
                            'rsi': rsi,
                            'sentiment': sentiment.get('label', 'NEUTRAL'),
                            'sentiment_score': sentiment.get('score', 0),
                            'has_catalyst': has_positive_catalyst,
                            'insider_signal': ticker_insider.get('signal', 'NEUTRAL'),
                            'reason': f"Market BULLISH but {ticker} down {pnl_pct:.1f}% with RSI {rsi:.0f}. "
                                     f"{'Positive catalyst detected! ' if has_positive_catalyst else ''}"
                                     f"No negative catalysts - HIGH CONVICTION dip buy.",
                            'action': f"ADD 20-30% to position at ${add_level:.2f} if it holds ${support_level:.2f} support",
                            'score': self._score_contrarian_opportunity(
                                rsi, sentiment.get('score', 0), has_positive_catalyst,
                                ticker_insider.get('signal', 'NEUTRAL')
                            )
                        })
                except Exception as e:
                    print(f"Error analyzing contrarian opportunity for {ticker}: {e}")
                    continue

        # Return sorted by score (highest conviction first)
        return sorted(opportunities, key=lambda x: x['score'], reverse=True)

    def _score_contrarian_opportunity(self, rsi: float, sentiment_score: float,
                                     has_catalyst: bool, insider_signal: str) -> float:
        """
        Score contrarian opportunities (higher = better buy)
        """
        score = 0.0

        # RSI scoring (lower RSI = higher score for dip buying)
        if rsi:
            if rsi < 25:      # Extremely oversold
                score += 0.4
            elif rsi < 30:    # Very oversold
                score += 0.3
            elif rsi < 35:    # Oversold
                score += 0.2

        # Sentiment scoring (positive sentiment during weakness = strong buy)
        if sentiment_score > 0.5:
            score += 0.3
        elif sentiment_score > 0:
            score += 0.15

        # Catalyst boost
        if has_catalyst:
            score += 0.2

        # Insider activity
        if insider_signal == 'BULLISH':
            score += 0.1

        return min(score, 1.0)

    async def _score_opportunity(self, opportunity: Dict) -> float:
        """
        Score an opportunity using multiple data sources
        """
        score = 0.0
        ticker = opportunity.get('symbol', '')

        try:
            # Volume score (30%)
            volume = opportunity.get('volume', 0)
            if volume > 5_000_000:
                score += 0.3
            elif volume > 2_000_000:
                score += 0.2
            elif volume > 1_000_000:
                score += 0.1

            # Price momentum score (20%)
            change_pct = opportunity.get('change_pct', 0)
            if abs(change_pct) > 10:
                score += 0.2
            elif abs(change_pct) > 5:
                score += 0.1

            # Get additional data for scoring
            try:
                # Technical score (20%)
                technicals = await self.market.get_technicals_alpha_vantage(ticker)
                rsi = technicals.get('rsi')
                if rsi:
                    if 30 < rsi < 70:  # Not overbought/oversold
                        score += 0.2
                    elif rsi < 30:  # Oversold - potential bounce
                        score += 0.15
            except:
                pass

            try:
                # News sentiment score (15%)
                news_data = await self.market.get_comprehensive_news([ticker])
                ticker_news = news_data.get(ticker, {})
                sentiment = ticker_news.get('sentiment', {})
                if sentiment.get('label') == 'POSITIVE':
                    score += 0.15
                elif sentiment.get('label') == 'NEUTRAL':
                    score += 0.05
            except:
                pass

            try:
                # Insider activity score (15%)
                insider_data = await self.market.get_insider_activity([ticker])
                ticker_insider = insider_data.get(ticker, {})
                if ticker_insider.get('signal') == 'BULLISH':
                    score += 0.15
                elif ticker_insider.get('signal') == 'NEUTRAL':
                    score += 0.05
            except:
                pass

        except Exception as e:
            print(f"Error scoring opportunity {ticker}: {e}")

        return min(score, 1.0)

    async def _generate_executive_summary(self, portfolio: Dict, regime: Dict, opportunities: List[Dict]) -> str:
        """
        Generate AI-powered executive summary
        """
        prompt = f"""
        Generate a concise executive summary (3-4 sentences) for a microcap trader:

        PORTFOLIO STATUS:
        - Total Value: ${portfolio['total_value']:,.2f}
        - Day P/L: ${portfolio['day_pl']:+,.2f} ({portfolio['day_pl_pct']:+.2f}%)
        - Positions: {len(portfolio['positions'])}

        MARKET REGIME:
        - Trend: {regime['trend']}
        - Volatility: {regime['volatility']}
        - Breadth: {regime['breadth']}
        - Confidence: {regime['confidence']:.0%}

        TOP OPPORTUNITIES FOUND: {len(opportunities)}

        Focus on: Today's key action items, market context, and biggest opportunities/risks.
        """

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def _generate_action_plan(self, portfolio: Dict, regime: Dict, opportunities: List[Dict]) -> str:
        """
        Generate AI-powered action plan
        """
        prompt = f"""
        Generate a prioritized action plan (5-7 bullet points) for today:

        MARKET REGIME: {regime['trend']} trend, {regime['volatility']} volatility

        PORTFOLIO: {len(portfolio['positions'])} positions, {portfolio['day_pl_pct']:+.2f}% today

        TOP OPPORTUNITIES: {len(opportunities)} high-probability setups identified

        Focus on: Immediate actions, position management, new entry opportunities, risk management.
        Be specific with tickers and price levels where possible.
        """

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _format_contrarian_opportunities(self, opportunities: List[Dict]) -> str:
        """Format contrarian dip-buy opportunities"""
        if not opportunities:
            return "**No contrarian opportunities detected.**\n\nMarket regime not bullish or all positions performing well."

        output = ["**🚀 AGGRESSIVE DIP-BUY SIGNALS - Market Strong, Your Stocks Weak**\n"]

        for i, opp in enumerate(opportunities, 1):
            ticker = opp['ticker']
            score = opp['score']
            rsi = opp['rsi']
            sentiment = opp['sentiment']
            pnl_pct = opp['pnl_pct']
            has_catalyst = opp.get('has_catalyst', False)

            # Emoji based on conviction score
            if score > 0.7:
                emoji = "🔥🔥🔥"  # Highest conviction
            elif score > 0.5:
                emoji = "🔥🔥"    # High conviction
            else:
                emoji = "🔥"      # Good conviction

            output.append(f"**{i}. {ticker}** {emoji} (Conviction: {score:.0%})")
            output.append(f"   - **Position**: Down {pnl_pct:.1f}% | RSI: {rsi:.0f} (OVERSOLD)")
            output.append(f"   - **Sentiment**: {sentiment} | {'✅ Catalyst Detected!' if has_catalyst else 'No negative news'}")
            output.append(f"   - **Signal**: {opp['reason']}")
            output.append(f"   - **🎯 ACTION**: {opp['action']}")
            output.append("")

        return "\n".join(output)

    def _format_sector_performance(self, sectors: Dict) -> str:
        """Format sector performance data"""
        if not sectors:
            return "No sector data available"

        # Handle market breadth data (what we actually get)
        if 'breadth_status' in sectors:
            positive = sectors.get('positive_sectors', 0)
            total = sectors.get('total_sectors', 0)
            ratio = sectors.get('breadth_ratio', 0)
            status = sectors.get('breadth_status', 'UNKNOWN')

            emoji = "🟢" if status == 'STRONG' else "🔴" if status == 'WEAK' else "⚪"
            return f"{emoji} **Market Breadth**: {status} ({positive}/{total} sectors positive, {ratio:.0%})"

        # Fallback for actual sector data if provided
        output = []
        for sector, data in list(sectors.items())[:5]:
            if isinstance(data, dict):
                change = data.get('changesPercentage', 0)
                emoji = "🟢" if change > 0 else "🔴"
                output.append(f"{emoji} **{sector}**: {change:+.2f}%")

        return "\n".join(output) if output else "No sector data available"

    def _format_unusual_activity(self, unusual: List[Dict]) -> str:
        """Format unusual volume activity"""
        if not unusual:
            return "No unusual activity detected"

        output = []
        for stock in unusual:
            ticker = stock.get('symbol', 'N/A')
            volume = stock.get('volume', 0)
            change = stock.get('change_pct', 0)
            output.append(f"- **{ticker}**: {volume:,.0f} vol, {change:+.2f}% change")

        return "\n".join(output)

    def _format_position_analyses(self, analyses: Dict[str, str]) -> str:
        """Format position analyses"""
        if not analyses:
            return "No positions analyzed"

        output = []
        for ticker, analysis in analyses.items():
            output.append(f"#### {ticker}\n{analysis}\n")

        return "\n".join(output)

    def _format_insider_activity(self, insiders: Dict) -> str:
        """Format insider activity data"""
        if not insiders:
            return "No insider activity data"

        output = []
        for ticker, data in insiders.items():
            signal = data.get('signal', 'NEUTRAL')
            buys = len(data.get('recent_buys', []))
            sells = len(data.get('recent_sells', []))

            if buys > 0 or sells > 0:
                emoji = "🟢" if signal == 'BULLISH' else "🔴" if signal == 'BEARISH' else "⚪"
                output.append(f"{emoji} **{ticker}**: {buys} buys, {sells} sells ({signal})")

        return "\n".join(output) if output else "No significant insider activity"

    def _format_finnhub_news(self, news: Dict) -> str:
        """Format Finnhub news"""
        if not news:
            return "No news available"

        output = []
        for ticker, data in list(news.items())[:3]:
            articles = data.get('articles', [])[:2]
            for article in articles:
                title = article.get('headline', article.get('title', 'No title'))
                output.append(f"- **{ticker}**: {title}")

        return "\n".join(output) if output else "No recent news"

    def _format_newsapi_sentiment(self, news: Dict) -> str:
        """Format NewsAPI sentiment"""
        if not news:
            return "No sentiment data available"

        output = []
        for ticker, data in news.items():
            sentiment = data.get('sentiment', {})
            label = sentiment.get('label', 'NEUTRAL')
            score = sentiment.get('score', 0)

            emoji = "🟢" if label == 'POSITIVE' else "🔴" if label == 'NEGATIVE' else "⚪"
            output.append(f"{emoji} **{ticker}**: {label} (score: {score:.2f})")

        return "\n".join(output) if output else "No sentiment data"

    async def _format_opportunities(self, opportunities: List[Dict]) -> str:
        """Format opportunities list"""
        if not opportunities:
            return "No high-probability setups identified"

        output = []
        for i, opp in enumerate(opportunities, 1):
            ticker = opp.get('symbol', 'N/A')
            score = opp.get('score', 0)
            volume = opp.get('volume', 0)
            change = opp.get('change_pct', 0)

            output.append(
                f"**{i}. {ticker}** (Score: {score:.0%})\n"
                f"   Volume: {volume:,.0f} | Change: {change:+.2f}%"
            )

        return "\n\n".join(output)


# Example usage adapter for existing infrastructure
class PortfolioServiceAdapter:
    """Adapter to make your existing portfolio data work with the report generator"""

    def __init__(self, alpaca_api):
        self.api = alpaca_api

    async def get_current_positions(self) -> Dict:
        """Adapt Alpaca data to expected format"""
        account = self.api.get_account()
        positions = self.api.list_positions()

        portfolio_value = float(account.portfolio_value)
        last_equity = float(account.last_equity)
        day_pl = portfolio_value - last_equity
        day_pl_pct = (day_pl / last_equity * 100) if last_equity > 0 else 0

        position_list = []
        tickers = []

        for pos in positions:
            tickers.append(pos.symbol)
            position_list.append({
                'symbol': pos.symbol,
                'shares': float(pos.qty),
                'entry': float(pos.avg_entry_price),
                'current': float(pos.current_price),
                'pnl_pct': float(pos.unrealized_plpc) * 100
            })

        return {
            'total_value': portfolio_value,
            'day_pl': day_pl,
            'day_pl_pct': day_pl_pct,
            'positions': position_list,
            'tickers': tickers
        }


class MarketServiceAdapter:
    """Adapter to make your MarketDataManager async-compatible"""

    def __init__(self, market_data_manager):
        self.mgr = market_data_manager

    async def get_spy_data(self):
        return await self.mgr.get_spy_data()

    async def get_futures(self):
        # Placeholder - implement if you have futures data
        return {'ES': 0.0, 'NQ': 0.0}

    async def get_sector_performance(self):
        return await self.mgr.get_market_breadth_fmp()

    async def scan_unusual_activity(self):
        return await self.mgr.scan_unusual_activity()

    async def get_comprehensive_news(self, tickers):
        return await self.mgr.get_comprehensive_news(tickers)

    async def get_insider_activity(self, tickers):
        return await self.mgr.get_insider_activity(tickers)

    async def analyze_market_regime(self):
        return await self.mgr.analyze_market_regime()

    async def get_fundamentals_fmp(self, ticker):
        if self.mgr.fmp:
            return self.mgr.fmp.get_company_profile(ticker)
        return {}

    async def get_technicals_alpha_vantage(self, ticker):
        if self.mgr.alpha_vantage:
            rsi = self.mgr.alpha_vantage.get_rsi(ticker)
            macd = self.mgr.alpha_vantage.get_macd(ticker)
            return {
                'rsi': rsi.get('rsi') if rsi else None,
                'macd': macd.get('macd') if macd else None
            }
        return {}

    async def get_options_flow_polygon(self, ticker):
        # Placeholder - implement if you have options data
        return {'unusual': False, 'put_call_ratio': 0}
