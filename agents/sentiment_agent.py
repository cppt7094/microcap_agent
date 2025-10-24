"""
Sentiment Analysis Agent

Analyzes news sentiment and social buzz.
Makes BUY/SELL/HOLD based on sentiment momentum.
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


class SentimentAgent:
    """
    Analyzes news sentiment and social buzz.
    Makes BUY/SELL/HOLD based on sentiment momentum.
    """

    def __init__(self, anthropic_api_key: str = None):
        """Initialize Sentiment Agent with data fetcher and Claude API"""
        self.data_fetcher = smart_fetcher
        self.directive = get_agent_directive("sentiment")

        # Initialize Claude API client
        api_key = anthropic_api_key or Config.ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("No Anthropic API key provided - agent will use fallback logic")
            self.anthropic_client = None
        else:
            self.anthropic_client = Anthropic(api_key=api_key)
            logger.info("Sentiment Agent initialized with Claude API")

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

    def _simple_sentiment_score(self, ticker: str, quote: Dict) -> tuple:
        """
        Simple sentiment heuristics when no news data available.

        For now, uses price momentum as proxy for sentiment.
        Future: integrate NewsAPI, Reddit sentiment, insider trading data.
        """
        # Use recent price action as sentiment proxy
        current_price = quote.get('close')
        prev_close = quote.get('prev_close')

        if current_price and prev_close:
            daily_change = ((current_price - prev_close) / prev_close) * 100

            if daily_change > 5:
                return 70, f"Strong positive momentum (+{daily_change:.1f}% today)"
            elif daily_change > 2:
                return 60, f"Positive momentum (+{daily_change:.1f}% today)"
            elif daily_change < -5:
                return 30, f"Strong negative momentum ({daily_change:.1f}% today)"
            elif daily_change < -2:
                return 40, f"Negative momentum ({daily_change:.1f}% today)"
            else:
                return 50, f"Neutral price action ({daily_change:+.1f}% today)"
        else:
            return 50, "No recent price data for sentiment analysis"

    def analyze(self, ticker: str, portfolio_context: Dict = None) -> Dict:
        """
        Analyze ticker from sentiment perspective.

        Args:
            ticker: Stock ticker symbol
            portfolio_context: Optional portfolio state for context

        Returns:
            {
                "ticker": "APLD",
                "action": "BUY" | "SELL" | "HOLD",
                "confidence": 65,  # 0-100
                "reasoning": "Positive social sentiment. Recent FDA approval news driving buzz.",
                "agent": "sentiment",
                "signals": {
                    "sentiment_score": 70,
                    "news_count": 5,
                    "social_buzz": "high"
                }
            }
        """

        logger.info(f"[SentimentAgent] Analyzing {ticker}")

        # Get quote data for price-based sentiment proxy
        try:
            quote = self.data_fetcher.get_quote_data(ticker)
        except Exception as e:
            logger.error(f"Failed to fetch quote for {ticker}: {e}")
            return {
                "ticker": ticker,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": f"Data fetch error: {str(e)}",
                "agent": "sentiment",
                "signals": {}
            }

        if not quote:
            logger.warning(f"No quote data for {ticker}")
            return {
                "ticker": ticker,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": "No data available for sentiment analysis",
                "agent": "sentiment",
                "signals": {}
            }

        # Generate simple sentiment score
        sentiment_score, sentiment_note = self._simple_sentiment_score(ticker, quote)

        # Determine action based on sentiment
        if sentiment_score >= 65:
            action = "BUY"
            confidence = sentiment_score
            reasoning = f"Positive sentiment for {ticker}. {sentiment_note}"
        elif sentiment_score <= 40:
            action = "SELL"
            confidence = 100 - sentiment_score  # Invert for SELL confidence
            reasoning = f"Negative sentiment for {ticker}. {sentiment_note}"
        else:
            action = "HOLD"
            confidence = 50
            reasoning = f"Neutral sentiment for {ticker}. {sentiment_note}"

        # If Claude API is available, enhance analysis
        if self.anthropic_client:
            try:
                prompt = f"""Analyze {ticker} from a SENTIMENT perspective.

Current Data:
- Price-based sentiment score: {sentiment_score}/100
- Recent price movement: {sentiment_note}

Note: This is a placeholder sentiment analysis based on price momentum.
Future versions will incorporate:
- News sentiment from NewsAPI
- Social media buzz from Reddit/Twitter
- Insider trading signals
- Short interest data

Provide recommendation in JSON format:
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0-100,
    "reasoning": "2-3 sentences on sentiment and momentum"
}}

Be conservative. Without real news data, don't overweight sentiment.
If price momentum is strong (>5%), that can indicate building sentiment.
If momentum is weak, default to HOLD with low confidence.

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
            "agent": "sentiment",
            "signals": {
                "sentiment_score": sentiment_score,
                "price_momentum": sentiment_note,
                "data_source": "price_proxy",  # Indicates this is price-based, not real sentiment
                "note": "Future: will integrate NewsAPI and social sentiment"
            }
        }


# Singleton instance
_sentiment_agent_instance = None

def get_sentiment_agent() -> SentimentAgent:
    """Get singleton instance of Sentiment Agent"""
    global _sentiment_agent_instance
    if _sentiment_agent_instance is None:
        _sentiment_agent_instance = SentimentAgent()
    return _sentiment_agent_instance


# Test script
if __name__ == "__main__":
    print("=" * 80)
    print("SENTIMENT AGENT - TEST")
    print("=" * 80)

    agent = get_sentiment_agent()

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
