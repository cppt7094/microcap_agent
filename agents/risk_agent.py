"""
Risk Analysis Agent

Evaluates portfolio risk, position sizing, correlation, and sector exposure.
Makes BUY/SELL/HOLD based on risk management principles.
"""

import sys
import os
import json
import logging
from typing import Dict, Optional
from anthropic import Anthropic

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.data_fetcher import smart_fetcher
from agents.core_directives import get_agent_directive
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskAgent:
    """
    Evaluates portfolio risk, position sizing, correlation, and sector exposure.
    Makes BUY/SELL/HOLD based on risk management principles.
    """

    def __init__(self, anthropic_api_key: str = None):
        """Initialize Risk Agent with data fetcher and Claude API"""
        self.data_fetcher = smart_fetcher
        self.directive = get_agent_directive("risk")

        # Initialize Claude API client
        api_key = anthropic_api_key or Config.ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("No Anthropic API key provided - agent will use fallback logic")
            self.anthropic_client = None
        else:
            self.anthropic_client = Anthropic(api_key=api_key)
            logger.info("Risk Agent initialized with Claude API")

    def _parse_json_response(self, text: str) -> Dict:
        """Extract JSON from Claude's response"""
        try:
            # Try to find JSON in the response
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.error(f"No JSON found in response: {text}")
                return {"action": "HOLD", "confidence": 50, "reasoning": "Failed to parse response"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {"action": "HOLD", "confidence": 50, "reasoning": "JSON parse error"}

    def _calculate_portfolio_risk(self, ticker: str, portfolio_context: Dict) -> Dict:
        """
        Calculate risk metrics based on portfolio context.

        Returns:
            {
                "total_positions": 5,
                "sector_exposure": 35,  # % of portfolio in same sector
                "position_concentration": 18,  # % of portfolio this position represents
                "risk_level": "medium"
            }
        """
        if not portfolio_context:
            return {
                "total_positions": 0,
                "sector_exposure": 0,
                "position_concentration": 0,
                "risk_level": "unknown"
            }

        total_value = portfolio_context.get('total_value', 0)
        positions = portfolio_context.get('positions', [])
        total_positions = len(positions)

        # Find ticker's fundamentals for sector info
        try:
            fundamentals = self.data_fetcher.get_fundamentals(ticker)
            ticker_sector = fundamentals.get('sector') if fundamentals else None
        except:
            ticker_sector = None

        # Calculate sector exposure
        sector_exposure = 0
        if ticker_sector and total_value > 0:
            sector_value = sum(
                pos.get('market_value', 0)
                for pos in positions
                if self._get_position_sector(pos.get('ticker')) == ticker_sector
            )
            sector_exposure = (sector_value / total_value) * 100

        # Determine risk level
        if total_positions >= 10:
            risk_level = "low"  # Well diversified
        elif total_positions >= 5:
            risk_level = "medium"
        else:
            risk_level = "high"  # Concentrated

        if sector_exposure > 40:
            risk_level = "high"  # Sector concentration risk

        return {
            "total_positions": total_positions,
            "sector_exposure": round(sector_exposure, 1),
            "ticker_sector": ticker_sector,
            "risk_level": risk_level
        }

    def _get_position_sector(self, ticker: str) -> Optional[str]:
        """Helper to get sector for a ticker"""
        try:
            fundamentals = self.data_fetcher.get_fundamentals(ticker)
            return fundamentals.get('sector') if fundamentals else None
        except:
            return None

    def analyze(self, ticker: str, portfolio_context: Dict = None) -> Dict:
        """
        Analyze ticker from risk management perspective.

        Args:
            ticker: Stock ticker symbol
            portfolio_context: Portfolio state (REQUIRED for meaningful risk analysis)

        Returns:
            {
                "ticker": "APLD",
                "action": "BUY" | "SELL" | "HOLD",
                "confidence": 70,  # 0-100
                "reasoning": "Portfolio already 35% tech sector. Adding more increases concentration risk.",
                "agent": "risk",
                "signals": {
                    "sector_exposure": 35,
                    "position_count": 5,
                    "risk_level": "medium"
                }
            }
        """

        logger.info(f"[RiskAgent] Analyzing {ticker}")

        # Calculate portfolio risk metrics
        risk_metrics = self._calculate_portfolio_risk(ticker, portfolio_context or {})

        # Default conservative stance
        action = "HOLD"
        confidence = 50

        # Simple risk rules
        if risk_metrics["risk_level"] == "high":
            action = "SELL"
            confidence = 65
            reasoning = f"High portfolio risk. {risk_metrics['total_positions']} positions with {risk_metrics['sector_exposure']:.1f}% sector exposure. Reduce concentration."
        elif risk_metrics["risk_level"] == "medium":
            action = "HOLD"
            confidence = 55
            reasoning = f"Moderate portfolio risk. {risk_metrics['total_positions']} positions. Monitor sector exposure ({risk_metrics['sector_exposure']:.1f}%)."
        else:
            action = "BUY"
            confidence = 60
            reasoning = f"Good diversification. {risk_metrics['total_positions']} positions with {risk_metrics['sector_exposure']:.1f}% sector exposure. Room to add."

        # If Claude API is available, enhance analysis
        if self.anthropic_client:
            try:
                prompt = f"""Analyze {ticker} from a RISK MANAGEMENT perspective.

Portfolio Context:
- Total Positions: {risk_metrics['total_positions']}
- Sector Exposure ({risk_metrics.get('ticker_sector', 'N/A')}): {risk_metrics['sector_exposure']:.1f}%
- Risk Level: {risk_metrics['risk_level']}

Risk Assessment:
- Is the portfolio over-concentrated in one sector?
- Should we add more exposure or reduce?
- What's the appropriate position size given current risk?

Provide recommendation in JSON format:
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0-100,
    "reasoning": "2-3 sentences on risk and position sizing"
}}

Be conservative. If sector exposure >40%, warn about concentration.
If <5 positions, that's high concentration risk.
If >10 positions with balanced sectors, that's healthy diversification.

No hedging language. Be direct."""

                # Call Claude API
                response = self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=500,
                    system=self.directive,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Parse response
                analysis_text = response.content[0].text
                analysis = self._parse_json_response(analysis_text)

                # Use Claude's analysis
                action = analysis["action"]
                confidence = analysis["confidence"]
                reasoning = analysis["reasoning"]

            except Exception as e:
                logger.error(f"Claude API error for {ticker}: {e}")
                # Keep fallback analysis

        # Build final response
        return {
            "ticker": ticker,
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "agent": "risk",
            "signals": {
                "total_positions": risk_metrics["total_positions"],
                "sector_exposure": risk_metrics["sector_exposure"],
                "sector": risk_metrics.get("ticker_sector"),
                "risk_level": risk_metrics["risk_level"]
            }
        }


# Singleton instance
_risk_agent_instance = None

def get_risk_agent() -> RiskAgent:
    """Get singleton instance of Risk Agent"""
    global _risk_agent_instance
    if _risk_agent_instance is None:
        _risk_agent_instance = RiskAgent()
    return _risk_agent_instance


# Test script
if __name__ == "__main__":
    print("=" * 80)
    print("RISK AGENT - TEST")
    print("=" * 80)

    agent = get_risk_agent()

    # Test with a real ticker and mock portfolio
    test_ticker = "APLD"
    mock_portfolio = {
        "total_value": 1000,
        "positions": [
            {"ticker": "APLD", "market_value": 200},
            {"ticker": "NTLA", "market_value": 200},
            {"ticker": "CRWV", "market_value": 200},
            {"ticker": "SOUN", "market_value": 200},
            {"ticker": "UUUU", "market_value": 200},
        ]
    }

    print(f"\nAnalyzing {test_ticker} with portfolio context...")

    result = agent.analyze(test_ticker, portfolio_context=mock_portfolio)

    print(f"\nRESULTS:")
    print(f"  Ticker: {result['ticker']}")
    print(f"  Action: {result['action']}")
    print(f"  Confidence: {result['confidence']}%")
    print(f"  Reasoning: {result['reasoning']}")
    print(f"  Agent: {result['agent']}")
    print(f"\nSignals:")
    for key, value in result['signals'].items():
        if value is not None:
            print(f"    {key}: {value}")

    print("\n" + "=" * 80)
