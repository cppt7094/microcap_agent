"""
Technical Analysis Agent

Analyzes price action, volume, RSI, MACD, moving averages.
Makes BUY/SELL/HOLD recommendations based on charts.
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


class TechnicalAgent:
    """
    Analyzes price action, volume, RSI, MACD, moving averages.
    Makes BUY/SELL/HOLD recommendations based on charts.
    """

    def __init__(self, anthropic_api_key: str = None):
        """Initialize Technical Agent with data fetcher and Claude API"""
        self.data_fetcher = smart_fetcher
        self.directive = get_agent_directive("technical")

        # Initialize Claude API client
        api_key = anthropic_api_key or Config.ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("No Anthropic API key provided - agent will use fallback logic")
            self.anthropic_client = None
        else:
            self.anthropic_client = Anthropic(api_key=api_key)
            logger.info("Technical Agent initialized with Claude API")

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

    def _fallback_analysis(self, ticker: str, technicals: Dict, quote: Dict) -> Dict:
        """Simple rule-based analysis when Claude API is unavailable"""
        rsi = technicals.get('rsi')
        macd = technicals.get('macd')
        macd_signal = technicals.get('macd_signal')

        # Simple technical rules
        action = "HOLD"
        confidence = 50
        reasoning = f"Technical analysis for {ticker}: "

        signals = []

        if rsi:
            if rsi > 70:
                signals.append(f"Overbought (RSI {rsi:.1f})")
                action = "SELL"
                confidence = 65
            elif rsi < 30:
                signals.append(f"Oversold (RSI {rsi:.1f})")
                action = "BUY"
                confidence = 65
            else:
                signals.append(f"Neutral RSI ({rsi:.1f})")

        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                signals.append("MACD bullish")
                if action == "HOLD":
                    action = "BUY"
                    confidence = 60
            elif macd < macd_signal:
                signals.append("MACD bearish")
                if action == "HOLD":
                    action = "SELL"
                    confidence = 60

        reasoning += ", ".join(signals) if signals else "No strong technical signals"

        return {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning
        }

    def analyze(self, ticker: str, portfolio_context: Dict = None) -> Dict:
        """
        Analyze ticker from technical perspective.

        Args:
            ticker: Stock ticker symbol
            portfolio_context: Optional portfolio state for context

        Returns:
            {
                "ticker": "APLD",
                "action": "BUY" | "SELL" | "HOLD",
                "confidence": 85,  # 0-100
                "reasoning": "RSI 65, MACD bullish crossover, breaking resistance",
                "agent": "technical",
                "signals": {
                    "rsi": 65,
                    "macd": 0.15,
                    "trend": "uptrend",
                    "source": "polygon"
                }
            }
        """

        logger.info(f"[TechnicalAgent] Analyzing {ticker}")

        # Get technical data
        try:
            technicals = self.data_fetcher.get_technical_indicators(ticker)
            quote = self.data_fetcher.get_quote_data(ticker)
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return {
                "ticker": ticker,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": f"Data fetch error: {str(e)}",
                "agent": "technical",
                "signals": {}
            }

        if not technicals or not quote:
            logger.warning(f"Insufficient data for {ticker}")
            return {
                "ticker": ticker,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": "Insufficient technical data available",
                "agent": "technical",
                "signals": {}
            }

        # If Claude API is available, use it for analysis
        if self.anthropic_client:
            try:
                # Build analysis prompt
                prompt = f"""Analyze {ticker} from a TECHNICAL perspective.

Technical Data:
- RSI: {technicals.get('rsi', 'N/A')}
- MACD: {technicals.get('macd', 'N/A')}
- MACD Signal: {technicals.get('macd_signal', 'N/A')}
- Current Price: ${quote.get('close', 'N/A')}
- Volume: {quote.get('volume', 'N/A')}
- Source: {technicals.get('source', 'N/A')}

Provide recommendation in JSON format:
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0-100,
    "reasoning": "2-3 sentences explaining the technical setup"
}}

Be brutally honest. If setup is weak, say HOLD or assign low confidence.
If RSI >70, warn about overbought condition.
If breaking resistance with volume, that's bullish.
If MACD crosses above signal line, that's a bullish signal.

No hedging language. Be direct and actionable."""

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
                analysis = self._fallback_analysis(ticker, technicals, quote)
        else:
            # Use fallback rule-based analysis
            analysis = self._fallback_analysis(ticker, technicals, quote)

        # Build final response
        return {
            "ticker": ticker,
            "action": analysis["action"],
            "confidence": analysis["confidence"],
            "reasoning": analysis["reasoning"],
            "agent": "technical",
            "signals": {
                "rsi": technicals.get('rsi'),
                "macd": technicals.get('macd'),
                "macd_signal": technicals.get('macd_signal'),
                "price": quote.get('close'),
                "volume": quote.get('volume'),
                "source": technicals.get('source')
            }
        }


# Singleton instance
_technical_agent_instance = None

def get_technical_agent() -> TechnicalAgent:
    """Get singleton instance of Technical Agent"""
    global _technical_agent_instance
    if _technical_agent_instance is None:
        _technical_agent_instance = TechnicalAgent()
    return _technical_agent_instance


# Test script
if __name__ == "__main__":
    print("=" * 80)
    print("TECHNICAL AGENT - TEST")
    print("=" * 80)

    agent = get_technical_agent()

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
        print(f"    {key}: {value}")

    print("\n" + "=" * 80)
