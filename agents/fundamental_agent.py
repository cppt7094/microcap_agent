"""
Fundamental Analysis Agent

Analyzes company fundamentals: revenue, P/E, growth, cash position.
Makes BUY/SELL/HOLD based on valuation and business quality.
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


class FundamentalAgent:
    """
    Analyzes company fundamentals: revenue, P/E, growth, cash position.
    Makes BUY/SELL/HOLD based on valuation and business quality.
    """

    def __init__(self, anthropic_api_key: str = None):
        """Initialize Fundamental Agent with data fetcher and Claude API"""
        self.data_fetcher = smart_fetcher
        self.directive = get_agent_directive("fundamental")

        # Initialize Claude API client
        api_key = anthropic_api_key or Config.ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("No Anthropic API key provided - agent will use fallback logic")
            self.anthropic_client = None
        else:
            self.anthropic_client = Anthropic(api_key=api_key)
            logger.info("Fundamental Agent initialized with Claude API")

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

    def _fallback_analysis(self, ticker: str, fundamentals: Dict) -> Dict:
        """Simple rule-based analysis when Claude API is unavailable"""
        pe_ratio = fundamentals.get('pe_ratio')
        market_cap = fundamentals.get('market_cap')

        action = "HOLD"
        confidence = 50
        reasoning = f"Fundamental analysis for {ticker}: "

        signals = []

        # Simple valuation rules
        if pe_ratio:
            if pe_ratio < 0:
                signals.append("Negative P/E (not profitable)")
                action = "SELL"
                confidence = 60
            elif pe_ratio < 15:
                signals.append(f"Undervalued (P/E {pe_ratio:.1f})")
                action = "BUY"
                confidence = 65
            elif pe_ratio > 50:
                signals.append(f"Overvalued (P/E {pe_ratio:.1f})")
                action = "SELL"
                confidence = 65
            else:
                signals.append(f"Fair valuation (P/E {pe_ratio:.1f})")

        if market_cap:
            if market_cap < 300_000_000:
                signals.append("Micro-cap (higher risk)")

        reasoning += ", ".join(signals) if signals else "Limited fundamental data available"

        return {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning
        }

    def analyze(self, ticker: str, portfolio_context: Dict = None) -> Dict:
        """
        Analyze ticker from fundamental perspective.

        Args:
            ticker: Stock ticker symbol
            portfolio_context: Optional portfolio state for context

        Returns:
            {
                "ticker": "APLD",
                "action": "BUY" | "SELL" | "HOLD",
                "confidence": 75,  # 0-100
                "reasoning": "P/E of 12 below sector average. Growing revenue but high debt.",
                "agent": "fundamental",
                "signals": {
                    "pe_ratio": 12.5,
                    "market_cap": 450000000,
                    "sector": "Technology",
                    "industry": "Software"
                }
            }
        """

        logger.info(f"[FundamentalAgent] Analyzing {ticker}")

        # Get fundamental data
        try:
            fundamentals = self.data_fetcher.get_fundamentals(ticker)
        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {ticker}: {e}")
            return {
                "ticker": ticker,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": f"Data fetch error: {str(e)}",
                "agent": "fundamental",
                "signals": {}
            }

        if not fundamentals:
            logger.warning(f"No fundamental data for {ticker}")
            return {
                "ticker": ticker,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": "No fundamental data available",
                "agent": "fundamental",
                "signals": {}
            }

        # If Claude API is available, use it for analysis
        if self.anthropic_client:
            try:
                # Build analysis prompt
                prompt = f"""Analyze {ticker} from a FUNDAMENTAL perspective.

Fundamental Data:
- P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}
- Market Cap: ${fundamentals.get('market_cap', 'N/A'):,} ({self._format_market_cap(fundamentals.get('market_cap'))})
- Sector: {fundamentals.get('sector', 'N/A')}
- Industry: {fundamentals.get('industry', 'N/A')}
- Description: {fundamentals.get('description', 'N/A')[:200]}...

Provide recommendation in JSON format:
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0-100,
    "reasoning": "2-3 sentences on valuation and business quality"
}}

Be harsh on valuation. If P/E > 50, flag as overvalued unless there's exceptional growth.
If P/E < 0 (unprofitable), that's a red flag for micro-caps.
If it's a speculative biotech or early-stage tech, acknowledge higher risk.

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

            except Exception as e:
                logger.error(f"Claude API error for {ticker}: {e}")
                # Fall back to rule-based analysis
                analysis = self._fallback_analysis(ticker, fundamentals)
        else:
            # Use fallback rule-based analysis
            analysis = self._fallback_analysis(ticker, fundamentals)

        # Build final response
        return {
            "ticker": ticker,
            "action": analysis["action"],
            "confidence": analysis["confidence"],
            "reasoning": analysis["reasoning"],
            "agent": "fundamental",
            "signals": {
                "pe_ratio": fundamentals.get('pe_ratio'),
                "market_cap": fundamentals.get('market_cap'),
                "sector": fundamentals.get('sector'),
                "industry": fundamentals.get('industry'),
                "description": fundamentals.get('description', '')[:100] + "..." if fundamentals.get('description') else None
            }
        }

    def _format_market_cap(self, market_cap: Optional[float]) -> str:
        """Format market cap for human readability"""
        if not market_cap:
            return "Unknown"

        if market_cap < 300_000_000:
            return "Micro-cap"
        elif market_cap < 2_000_000_000:
            return "Small-cap"
        elif market_cap < 10_000_000_000:
            return "Mid-cap"
        else:
            return "Large-cap"


# Singleton instance
_fundamental_agent_instance = None

def get_fundamental_agent() -> FundamentalAgent:
    """Get singleton instance of Fundamental Agent"""
    global _fundamental_agent_instance
    if _fundamental_agent_instance is None:
        _fundamental_agent_instance = FundamentalAgent()
    return _fundamental_agent_instance


# Test script
if __name__ == "__main__":
    print("=" * 80)
    print("FUNDAMENTAL AGENT - TEST")
    print("=" * 80)

    agent = get_fundamental_agent()

    # Test with a real ticker
    test_ticker = "APLD"
    print(f"\nAnalyzing {test_ticker}...")

    result = agent.analyze(test_ticker)

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
