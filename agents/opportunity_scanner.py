"""
Opportunity Scanner Agent

Scans the market for high-potential microcap opportunities based on
technical indicators, momentum, fundamentals, and sector preferences.

SCORING PHILOSOPHY:
Scoring is intentionally HARSH. This is not a hype machine.
- 90-100: Exceptional, rare, slam dunk (should be <5% of scans)
- 80-89: Strong opportunity, clear edge (~10% of scans)
- 70-79: Decent setup, worth considering (~20% of scans)
- 60-69: Marginal, probably skip (~30% of scans)
- <60: Weak, filtered out (~35% of scans)

If you're scoring 80+ regularly, you're inflating scores and destroying
the value of the system. High scores must MEAN something.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import time
import json
from pathlib import Path
import yfinance as yf
from agents.core_directives import get_agent_directive, get_scoring_guidelines

# Configure logging
logger = logging.getLogger(__name__)

# Investment Profile & Screening Criteria
SCREENING_CRITERIA = {
    "market_cap": {"min": 50_000_000, "max": 2_000_000_000},  # $50M-$2B
    "sectors": ["Technology", "Healthcare", "Biotechnology", "Energy"],
    "price_range": {"min": 2.0, "max": 50.0},
    "volume_min": 100_000,  # shares/day
    "technicals": {
        "rsi_min": 25,
        "rsi_max": 75,
        "price_change_min": 1.0,  # % today (more lenient)
        "price_change_max": 25.0  # Allow higher volatility
    }
}

# Test universe of microcap tickers across preferred sectors
TEST_TICKER_UNIVERSE = [
    # Technology
    "TSLA", "NVDA", "AMD", "PLTR", "SOFI", "RIVN", "LCID", "NIO", "PLUG", "FCEL",
    # Biotechnology & Healthcare
    "SOUN", "APLD", "NTLA", "CRSP", "EDIT", "BEAM", "BLUE", "RGNX", "FATE", "VERV",
    # Energy (Nuclear & Uranium)
    "UUUU", "CCJ", "DNN", "UEC", "URG", "PALAF", "LEU", "SMR", "OKLO", "NNE",
    # Space & Satellite
    "CRWV", "GSAT", "IRDM", "VSAT", "SATS", "GILT", "ASTS", "LUNR", "RKLB", "SPCE"
]


class OpportunityScannerAgent:
    """
    Scans market for high-potential opportunities based on momentum,
    technicals, fundamentals, and sector preferences.
    """

    # Scoring weights (must sum to 100)
    SCORING_WEIGHTS = {
        "momentum": 25,      # 25% - Price action, volume, breakouts
        "technical": 25,     # 25% - RSI, MACD, moving averages
        "fundamental": 25,   # 25% - Growth, valuation, cash position
        "sentiment": 10,     # 10% - News sentiment, insider activity
        "sector": 15         # 15% - Preferred sectors bonus
    }

    def __init__(self):
        """Initialize the Opportunity Scanner Agent."""
        self.name = "opportunity_scanner"
        self.criteria = SCREENING_CRITERIA
        self.last_scan_stats = {}  # Track scan statistics

        # Verify scoring weights sum to 100
        total_weight = sum(self.SCORING_WEIGHTS.values())
        if total_weight != 100:
            raise ValueError(f"Scoring weights must sum to 100, got {total_weight}")

        # Load cached stats if available
        self._load_cached_stats()

        logger.info(f"🔍 {self.name} initialized with {len(TEST_TICKER_UNIVERSE)} tickers in universe")

    def _load_cached_stats(self):
        """Load scan stats from cache file if it exists."""
        try:
            cache_file = Path("opportunities_latest.json")
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    self.last_scan_stats = data.get("stats", {})
                    logger.debug(f"Loaded cached scan stats from {cache_file}")
        except Exception as e:
            logger.debug(f"Could not load cached stats: {e}")

    def scan_for_opportunities(self, max_results: int = 10) -> List[Dict]:
        """
        Scan the market for top opportunities.

        Args:
            max_results: Maximum number of opportunities to return

        Returns:
            List of opportunity dicts sorted by score (highest first)
        """
        start_time = time.time()
        logger.info(f"🔍 Starting opportunity scan (max_results={max_results})...")

        universe = self._get_ticker_universe()
        logger.info(f"📊 Scanning {len(universe)} tickers...")

        opportunities = []
        filtered_count = 0
        error_count = 0

        for ticker in universe:
            try:
                # Apply quick filters
                ticker_data = self._fetch_ticker_data(ticker)
                if not ticker_data:
                    error_count += 1
                    continue

                if not self._apply_filters(ticker, ticker_data):
                    filtered_count += 1
                    continue

                # Score the opportunity
                score, signals = self._score_opportunity(ticker, ticker_data)

                # Harsh threshold - only show opportunities worth considering
                # Most scans should return 0-5 results, not dozens
                if score >= 60:  # Increased from 40 - be selective
                    opportunity = {
                        "ticker": ticker,
                        "score": score,
                        "price": ticker_data.get("price", 0),
                        "market_cap": ticker_data.get("market_cap", 0),
                        "sector": ticker_data.get("sector", "Unknown"),
                        "signals": signals,
                        "recommendation": self._get_recommendation(score),
                        "target_price": self._calculate_target_price(ticker_data, score),
                        "reasoning": self._generate_reasoning(ticker, score, signals, ticker_data),
                        "source": "yfinance",
                        "scanned_at": datetime.utcnow().isoformat() + "Z"
                    }
                    opportunities.append(opportunity)
                    logger.info(f"✅ {ticker}: Score {score} - {opportunity['recommendation']}")
                else:
                    filtered_count += 1

            except Exception as e:
                logger.error(f"❌ Error scanning {ticker}: {e}")
                error_count += 1
                continue

        # Sort by score descending
        opportunities.sort(key=lambda x: x["score"], reverse=True)

        # Calculate scan time
        scan_time = time.time() - start_time

        logger.info(f"📈 Scan complete: {len(opportunities)} opportunities found")
        logger.info(f"   - Filtered out: {filtered_count} tickers")
        logger.info(f"   - Errors: {error_count} tickers")
        logger.info(f"   - Scan time: {scan_time:.2f}s")

        # Update scan statistics
        self.last_scan_stats = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tickers_scanned": len(universe),
            "opportunities_found": len(opportunities),
            "filtered_count": filtered_count,
            "error_count": error_count,
            "scan_time": f"{scan_time:.2f}s"
        }

        # Save to cache file
        self._save_to_cache(opportunities[:max_results])

        return opportunities[:max_results]

    def _get_ticker_universe(self) -> List[str]:
        """
        Get the universe of tickers to scan.

        Returns:
            List of ticker symbols
        """
        return TEST_TICKER_UNIVERSE

    def _fetch_ticker_data(self, ticker: str) -> Optional[Dict]:
        """
        Fetch basic data for a ticker using yfinance.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with ticker data or None if fetch fails
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="5d")

            if hist.empty or len(hist) < 2:
                logger.warning(f"⚠️  {ticker}: Insufficient price history")
                return None

            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
            volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].mean() if len(hist) > 1 else volume

            # Calculate price change
            price_change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            # Calculate simple RSI
            rsi = self._calculate_rsi(hist['Close'].values) if len(hist) >= 14 else 50

            data = {
                "price": float(current_price),
                "prev_close": float(prev_close),
                "volume": int(volume),
                "avg_volume": int(avg_volume),
                "price_change_pct": float(price_change_pct),
                "market_cap": info.get("marketCap", 0),
                "sector": info.get("sector", "Unknown"),
                "pe_ratio": info.get("trailingPE", None),
                "forward_pe": info.get("forwardPE", None),
                "price_to_book": info.get("priceToBook", None),
                "revenue_growth": info.get("revenueGrowth", None),
                "rsi": float(rsi),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", None),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", None)
            }

            return data

        except Exception as e:
            logger.error(f"❌ Error fetching data for {ticker}: {e}")
            return None

    def _calculate_rsi(self, prices, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            prices: Array of closing prices
            period: RSI period (default 14)

        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral if not enough data

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _apply_filters(self, ticker: str, data: Dict) -> bool:
        """
        Apply screening filters to a ticker.

        Args:
            ticker: Stock symbol
            data: Ticker data dict

        Returns:
            True if ticker passes all filters
        """
        # Market cap filter
        market_cap = data.get("market_cap", 0)
        if market_cap < self.criteria["market_cap"]["min"] or market_cap > self.criteria["market_cap"]["max"]:
            return False

        # Price range filter
        price = data.get("price", 0)
        if price < self.criteria["price_range"]["min"] or price > self.criteria["price_range"]["max"]:
            return False

        # Volume filter
        volume = data.get("volume", 0)
        if volume < self.criteria["volume_min"]:
            return False

        # RSI filter (avoid extreme overbought/oversold)
        rsi = data.get("rsi", 50)
        if rsi < self.criteria["technicals"]["rsi_min"] or rsi > self.criteria["technicals"]["rsi_max"]:
            return False

        # Price change filter (only significant movers)
        price_change = abs(data.get("price_change_pct", 0))
        if price_change < self.criteria["technicals"]["price_change_min"]:
            return False
        if price_change > self.criteria["technicals"]["price_change_max"]:
            return False  # Too volatile

        return True

    def _score_opportunity(self, ticker: str, data: Dict) -> tuple[int, Dict]:
        """
        Score an opportunity from 0-100 based on weighted factors.

        SCORING BREAKDOWN (HARSH):
        - Momentum (25%): Price action, volume, breakouts
        - Technical (25%): RSI, MACD, moving averages
        - Fundamental (25%): Growth, valuation, cash position
        - Sentiment (10%): News sentiment, insider activity
        - Sector Match (15%): Preferred sectors bonus

        Total: 100 points

        HARSH PHILOSOPHY:
        - 85+ means this is exceptional (rare, <5% of scans)
        - Most good opportunities score 65-75
        - Don't inflate scores to look impressive
        - High scores must mean something

        Args:
            ticker: Stock symbol
            data: Ticker data dict

        Returns:
            Tuple of (score, signals_dict)
        """
        signals = {
            "momentum": 0,
            "technical": 0,
            "fundamental": 0,
            "sentiment": 0,
            "sector_match": 0
        }

        # 1. Momentum Score (0-25 max) - BE HARSH
        price_change = data.get("price_change_pct", 0)
        volume = data.get("volume", 0)
        avg_volume = data.get("avg_volume", 1)

        # Price momentum (0-15) - Harsh thresholds
        if price_change > 10:  # Exceptional move
            signals["momentum"] += 15
        elif price_change > 7:  # Strong move
            signals["momentum"] += 10
        elif price_change > 4:  # Decent move
            signals["momentum"] += 5
        # Below 4% doesn't count as momentum

        # Volume spike (0-10) - Harsh thresholds
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        if volume_ratio > 4:  # Exceptional volume
            signals["momentum"] += 10
        elif volume_ratio > 2.5:  # Strong volume
            signals["momentum"] += 7
        elif volume_ratio > 1.8:  # Above average volume
            signals["momentum"] += 4
        # Below 1.8x doesn't count as volume spike

        # 2. Technical Score (0-25 max)
        rsi = data.get("rsi", 50)
        price = data.get("price", 0)
        high_52w = data.get("fifty_two_week_high", price)
        low_52w = data.get("fifty_two_week_low", price)

        # RSI positioning (0-10 max) - Harsh: only perfect positioning gets full points
        if 58 <= rsi <= 65:  # Sweet spot - bullish but not overbought
            signals["technical"] += 10
        elif 52 <= rsi <= 70:
            signals["technical"] += 6
        elif 45 <= rsi <= 52:
            signals["technical"] += 3
        # Outside these ranges gets 0

        # 52-week position (0-15 max) - Harsh: near highs is good, middle is meh
        if high_52w and low_52w and high_52w != low_52w:
            position = (price - low_52w) / (high_52w - low_52w) * 100
            if position > 85:  # Very near highs (strength)
                signals["technical"] += 15
            elif position > 70:  # Near highs
                signals["technical"] += 10
            elif position > 55:  # Above middle
                signals["technical"] += 5
            # Below 55% of range doesn't get points

        # Cap technical at 25
        signals["technical"] = min(signals["technical"], self.SCORING_WEIGHTS["technical"])

        # Cap momentum at 25
        signals["momentum"] = min(signals["momentum"], self.SCORING_WEIGHTS["momentum"])

        # 3. Fundamental Score (0-25 max)
        pe_ratio = data.get("pe_ratio")
        forward_pe = data.get("forward_pe")
        pb_ratio = data.get("price_to_book")
        revenue_growth = data.get("revenue_growth")

        # P/E ratio (0-10 max)
        if pe_ratio and 0 < pe_ratio < 25:  # Reasonable valuation
            signals["fundamental"] += 10
        elif pe_ratio and 0 < pe_ratio < 40:
            signals["fundamental"] += 5
        elif forward_pe and 0 < forward_pe < 20:
            signals["fundamental"] += 7

        # Price to Book (0-8 max)
        if pb_ratio and 0 < pb_ratio < 3:  # Not overvalued
            signals["fundamental"] += 8
        elif pb_ratio and 0 < pb_ratio < 5:
            signals["fundamental"] += 4

        # Revenue Growth (0-7 max)
        if revenue_growth and revenue_growth > 0.20:  # 20%+ growth
            signals["fundamental"] += 7
        elif revenue_growth and revenue_growth > 0.10:
            signals["fundamental"] += 4

        # Cap fundamental at 25
        signals["fundamental"] = min(signals["fundamental"], self.SCORING_WEIGHTS["fundamental"])

        # 4. Sentiment Score (0-10 max) - Placeholder for now
        signals["sentiment"] = 0  # TODO: Add news sentiment analysis
        # Cap sentiment at 10
        signals["sentiment"] = min(signals["sentiment"], self.SCORING_WEIGHTS["sentiment"])

        # 5. Sector Match (0-15 max)
        sector = data.get("sector", "Unknown")
        if sector in self.criteria["sectors"]:
            signals["sector_match"] = 15
        # Cap sector at 15
        signals["sector_match"] = min(signals["sector_match"], self.SCORING_WEIGHTS["sector"])

        # Calculate total score
        total_score = sum(signals.values())

        # Safety check: ensure total doesn't exceed 100
        if total_score > 100:
            logger.error(f"{ticker}: Score overflow {total_score} > 100. Capping at 100.")
            logger.error(f"  Breakdown: {signals}")
            total_score = 100

        return total_score, signals

    def _get_recommendation(self, score: int) -> str:
        """
        Get recommendation based on score.

        HARSH RECOMMENDATIONS:
        - Strong Buy is RARE (85+)
        - Most recommendations are "Consider" or "Watch"
        - This maintains the value of high scores

        Args:
            score: Opportunity score (0-100)

        Returns:
            Recommendation string
        """
        if score >= 85:
            return "Strong Buy"  # Rare - exceptional opportunity
        elif score >= 75:
            return "Buy"  # Strong setup
        elif score >= 65:
            return "Consider"  # Decent setup
        elif score >= 60:
            return "Watch"  # Marginal
        else:
            return "Skip"  # Shouldn't see this (filtered at 60)

    def _calculate_target_price(self, data: Dict, score: int) -> float:
        """
        Calculate target price based on score and momentum.

        Args:
            data: Ticker data dict
            score: Opportunity score

        Returns:
            Target price
        """
        current_price = data.get("price", 0)
        if current_price == 0:
            return 0

        # Simple target: 5-20% upside based on score
        if score >= 80:
            upside = 0.20  # 20%
        elif score >= 70:
            upside = 0.15  # 15%
        elif score >= 60:
            upside = 0.10  # 10%
        else:
            upside = 0.05  # 5%

        target_price = current_price * (1 + upside)
        return round(target_price, 2)

    def _generate_reasoning(self, ticker: str, score: int, signals: Dict, data: Dict) -> str:
        """
        Generate human-readable reasoning for the opportunity.

        Uses brutal honesty framework - direct, actionable, no fluff.

        NOTE: This is template-based for now. In future, this could use
        Claude API with get_agent_directive("scanner") for AI-generated
        reasoning that follows the brutal honesty framework.

        Args:
            ticker: Stock symbol
            score: Total score
            signals: Breakdown of signal scores
            data: Ticker data

        Returns:
            Reasoning string (direct, no hedging)
        """
        reasons = []

        # Momentum reasoning - BE DIRECT
        if signals["momentum"] >= 15:
            price_change = data.get("price_change_pct", 0)
            volume_ratio = data.get("volume", 0) / data.get("avg_volume", 1)
            if volume_ratio > 2:
                reasons.append(f"Strong momentum with +{price_change:.1f}% on {volume_ratio:.1f}x volume")
            else:
                reasons.append(f"Solid price momentum: +{price_change:.1f}%")

        # Technical reasoning
        if signals["technical"] >= 15:
            rsi = data.get("rsi", 50)
            price = data.get("price", 0)
            high_52w = data.get("fifty_two_week_high", price)
            if high_52w and price / high_52w > 0.8:
                reasons.append(f"Near 52-week high with RSI at {rsi:.0f}")
            else:
                reasons.append(f"Favorable technical setup (RSI: {rsi:.0f})")

        # Fundamental reasoning
        if signals["fundamental"] >= 12:
            pe_ratio = data.get("pe_ratio")
            revenue_growth = data.get("revenue_growth")
            if revenue_growth and revenue_growth > 0.15:
                reasons.append(f"Strong revenue growth ({revenue_growth*100:.0f}%)")
            elif pe_ratio and 0 < pe_ratio < 25:
                reasons.append(f"Attractive valuation (P/E: {pe_ratio:.1f})")

        # Sector reasoning
        if signals["sector_match"] == 15:
            sector = data.get("sector", "Unknown")
            reasons.append(f"Preferred sector: {sector}")

        # Default if no specific reasons - be honest about it
        if not reasons:
            if score >= 70:
                reasons.append(f"Solid setup (score {score}), no standout catalyst")
            elif score >= 60:
                reasons.append(f"Marginal setup (score {score}), watch for confirmation")
            else:
                reasons.append(f"Weak setup (score {score}), skip")

        # Direct, no fluff formatting
        return ". ".join(reasons) + "."

    def _save_to_cache(self, opportunities: List[Dict]) -> None:
        """
        Save scan results to opportunities_latest.json for fast retrieval.

        Args:
            opportunities: List of opportunity dicts to save
        """
        try:
            cache_file = Path("opportunities_latest.json")
            data = {
                "opportunities": opportunities,
                "scanned_at": datetime.utcnow().isoformat() + "Z",
                "stats": self.last_scan_stats
            }

            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"💾 Saved {len(opportunities)} opportunities to {cache_file}")

        except Exception as e:
            logger.error(f"Failed to save opportunities cache: {e}")


# Singleton instance
_scanner_instance = None

def get_scanner() -> OpportunityScannerAgent:
    """Get or create the singleton scanner instance."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = OpportunityScannerAgent()
    return _scanner_instance


# Verification test
if __name__ == "__main__":
    print("=" * 80)
    print("OPPORTUNITY SCANNER - SCORING VERIFICATION")
    print("=" * 80)

    # Verify scoring weights sum to 100
    weights = OpportunityScannerAgent.SCORING_WEIGHTS
    total = sum(weights.values())

    print("\nScoring Weights:")
    for category, weight in weights.items():
        print(f"  {category:12} - {weight:2} points ({weight}%)")

    print(f"\nTotal: {total} points")

    assert total == 100, f"ERROR: Scoring weights sum to {total}, not 100!"
    print("\n[OK] Scoring weights verified: Totals exactly 100 points")

    # Test scanner initialization
    print("\nInitializing scanner...")
    scanner = OpportunityScannerAgent()
    print(f"[OK] Scanner initialized: {scanner.name}")

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
