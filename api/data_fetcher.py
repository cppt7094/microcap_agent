"""
Smart Data Fetcher with Fallback Logic
Provides robust data fetching across multiple sources with intelligent fallbacks
"""

import logging
import sys
import os
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_clients import FMPAPIClient, AlphaVantageClient
from api.cache_manager import cache_manager
from api.usage_tracker import usage_tracker
from config import Config
import alpaca_trade_api as tradeapi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlpacaClient:
    """Wrapper for Alpaca Trading API"""

    def __init__(self, api_key: str, secret_key: str, base_url: str):
        """Initialize Alpaca client"""
        try:
            self.api = tradeapi.REST(
                api_key,
                secret_key,
                base_url,
                api_version='v2'
            )
            logger.info("Alpaca client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca client: {e}")
            self.api = None

    def get_latest_quote(self, ticker: str) -> Optional[Dict]:
        """Get latest quote for a ticker"""
        if not self.api:
            return None

        try:
            quote = self.api.get_latest_trade(ticker)
            return {
                'price': float(quote.price),
                'size': int(quote.size),
                'timestamp': quote.timestamp.isoformat() if hasattr(quote.timestamp, 'isoformat') else str(quote.timestamp)
            }
        except Exception as e:
            logger.error(f"Alpaca quote error for {ticker}: {e}")
            return None

    def get_bars(self, ticker: str, timeframe='1Day', limit=30) -> Optional[Dict]:
        """Get OHLCV bars for a ticker"""
        if not self.api:
            return None

        try:
            bars = self.api.get_bars(
                ticker,
                timeframe,
                limit=limit
            )

            if not bars or len(bars) == 0:
                return None

            latest_bar = bars[-1]
            return {
                'open': float(latest_bar.o),
                'high': float(latest_bar.h),
                'low': float(latest_bar.l),
                'close': float(latest_bar.c),
                'volume': int(latest_bar.v),
                'timestamp': latest_bar.t.isoformat() if hasattr(latest_bar.t, 'isoformat') else str(latest_bar.t)
            }
        except Exception as e:
            logger.error(f"Alpaca bars error for {ticker}: {e}")
            return None


class SmartDataFetcher:
    """
    Smart data fetcher with comprehensive fallback logic across multiple data sources
    Tracks usage statistics and provides robust error handling
    """

    def __init__(self):
        """Initialize all API clients and usage tracking"""
        # Initialize API clients
        self.alpaca = None
        self.alpha_vantage = None
        self.fmp = None

        # Try to initialize Alpaca
        try:
            if Config.ALPACA_API_KEY and Config.ALPACA_SECRET_KEY:
                self.alpaca = AlpacaClient(
                    Config.ALPACA_API_KEY,
                    Config.ALPACA_SECRET_KEY,
                    Config.ALPACA_BASE_URL
                )
        except Exception as e:
            logger.warning(f"Alpaca client initialization failed: {e}")

        # Try to initialize Alpha Vantage
        try:
            if hasattr(Config, 'ALPHA_VANTAGE_KEY') and Config.ALPHA_VANTAGE_KEY:
                self.alpha_vantage = AlphaVantageClient(Config.ALPHA_VANTAGE_KEY)
        except Exception as e:
            logger.warning(f"Alpha Vantage client initialization failed: {e}")

        # Try to initialize FMP
        try:
            if hasattr(Config, 'FMP_API_KEY') and Config.FMP_API_KEY:
                self.fmp = FMPAPIClient(Config.FMP_API_KEY)
        except Exception as e:
            logger.warning(f"FMP client initialization failed: {e}")

        # Usage statistics tracking
        self.usage_stats = {
            "alpaca": {"success": 0, "failure": 0},
            "alpha_vantage": {"success": 0, "failure": 0},
            "fmp": {"success": 0, "failure": 0},
            "yfinance": {"success": 0, "failure": 0},
            "cache": {"success": 0, "failure": 0}
        }

        logger.info("SmartDataFetcher initialized")

    def _track_success(self, source: str):
        """Track successful data fetch"""
        if source in self.usage_stats:
            self.usage_stats[source]["success"] += 1

    def _track_failure(self, source: str):
        """Track failed data fetch"""
        if source in self.usage_stats:
            self.usage_stats[source]["failure"] += 1

    def get_usage_stats(self) -> Dict:
        """Get usage statistics across all data sources"""
        return self.usage_stats.copy()

    def get_current_price(self, ticker: str) -> Optional[Dict]:
        """
        Get current price with fallback chain:
        1. Try Alpaca
        2. If fails, try yfinance
        3. If fails, try cache (allow stale data)

        Returns:
            Dictionary with price, source, timestamp, and staleness indicator
        """
        logger.info(f"Fetching current price for {ticker}")

        # Try Alpaca first
        try:
            logger.info(f"  Attempting Alpaca for {ticker}")
            if self.alpaca:
                quote_data = self.alpaca.get_latest_quote(ticker)
                if quote_data:
                    self._track_success("alpaca")
                    usage_tracker.increment("alpaca")  # Track API usage
                    return {
                        "price": quote_data['price'],
                        "source": "alpaca",
                        "timestamp": quote_data['timestamp'],
                        "is_stale": False
                    }
            self._track_failure("alpaca")
        except Exception as e:
            logger.warning(f"  Alpaca failed for {ticker}: {e}")
            self._track_failure("alpaca")

        # Try yfinance
        try:
            logger.info(f"  Attempting yfinance for {ticker}")
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            if 'currentPrice' in info and info['currentPrice']:
                price = float(info['currentPrice'])
            elif 'regularMarketPrice' in info and info['regularMarketPrice']:
                price = float(info['regularMarketPrice'])
            else:
                raise ValueError("No price data in yfinance info")

            self._track_success("yfinance")
            usage_tracker.increment("yfinance")  # Track API usage
            return {
                "price": price,
                "source": "yfinance",
                "timestamp": datetime.now().isoformat(),
                "is_stale": False
            }
        except Exception as e:
            logger.warning(f"  yfinance failed for {ticker}: {e}")
            self._track_failure("yfinance")

        # Try cache (allow stale data)
        try:
            logger.info(f"  Attempting cache for {ticker}")
            cache_key = f"price_{ticker}"
            cached_data = cache_manager.cache.get(cache_key, max_age_minutes=1440)  # Allow 24h old data

            if cached_data:
                self._track_success("cache")
                usage_tracker.increment("cache")  # Track cache usage
                logger.info(f"  Using stale cached data for {ticker}")
                return {
                    **cached_data,
                    "source": "cache",
                    "is_stale": True
                }
            self._track_failure("cache")
        except Exception as e:
            logger.warning(f"  Cache failed for {ticker}: {e}")
            self._track_failure("cache")

        logger.error(f"All sources failed for {ticker} price")
        return None

    def get_quote_data(self, ticker: str) -> Optional[Dict]:
        """
        Get OHLCV data with fallback:
        1. Try Alpaca
        2. If fails, try yfinance
        3. If fails, try cache

        Returns:
            Dictionary with OHLCV data, source, and timestamp
        """
        logger.info(f"Fetching quote data for {ticker}")

        # Try Alpaca first
        try:
            logger.info(f"  Attempting Alpaca bars for {ticker}")
            if self.alpaca:
                bars_data = self.alpaca.get_bars(ticker)
                if bars_data:
                    self._track_success("alpaca")
                    usage_tracker.increment("alpaca")  # Track API usage
                    result = {
                        **bars_data,
                        "source": "alpaca"
                    }
                    # Cache the result
                    cache_manager.cache.set(f"quote_{ticker}", result)
                    return result
            self._track_failure("alpaca")
        except Exception as e:
            logger.warning(f"  Alpaca bars failed for {ticker}: {e}")
            self._track_failure("alpaca")

        # Try yfinance
        try:
            logger.info(f"  Attempting yfinance history for {ticker}")
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")

            if not hist.empty:
                latest = hist.iloc[-1]
                self._track_success("yfinance")
                usage_tracker.increment("yfinance")  # Track API usage
                result = {
                    "open": float(latest['Open']),
                    "high": float(latest['High']),
                    "low": float(latest['Low']),
                    "close": float(latest['Close']),
                    "volume": int(latest['Volume']),
                    "source": "yfinance",
                    "timestamp": datetime.now().isoformat()
                }
                # Cache the result
                cache_manager.cache.set(f"quote_{ticker}", result)
                return result
            else:
                raise ValueError("Empty history from yfinance")
        except Exception as e:
            logger.warning(f"  yfinance history failed for {ticker}: {e}")
            self._track_failure("yfinance")

        # Try cache
        try:
            logger.info(f"  Attempting cache for {ticker}")
            cache_key = f"quote_{ticker}"
            cached_data = cache_manager.cache.get(cache_key, max_age_minutes=1440)

            if cached_data:
                self._track_success("cache")
                usage_tracker.increment("cache")  # Track cache usage
                logger.info(f"  Using cached quote data for {ticker}")
                return {
                    **cached_data,
                    "source": "cache",
                    "is_stale": True
                }
            self._track_failure("cache")
        except Exception as e:
            logger.warning(f"  Cache failed for {ticker}: {e}")
            self._track_failure("cache")

        logger.error(f"All sources failed for {ticker} quote data")
        return None

    def get_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Get fundamental data with fallback:
        1. Try FMP if available
        2. If fails, try yfinance.Ticker(ticker).info
        3. If fails, try cache

        Returns:
            Dictionary with PE ratio, market cap, dividend yield, sector, industry
        """
        logger.info(f"Fetching fundamentals for {ticker}")

        # Try FMP first
        try:
            logger.info(f"  Attempting FMP for {ticker}")
            if self.fmp:
                profile = self.fmp.get_company_profile(ticker)
                if profile:
                    self._track_success("fmp")
                    usage_tracker.increment("fmp")  # Track API usage
                    result = {
                        "pe_ratio": profile.get('pe_ratio'),
                        "market_cap": profile.get('market_cap'),
                        "dividend_yield": None,  # FMP profile doesn't include this
                        "sector": profile.get('sector'),
                        "industry": profile.get('industry'),
                        "source": "fmp"
                    }
                    # Cache the result
                    cache_manager.cache.set(f"fundamentals_{ticker}", result)
                    return result
            self._track_failure("fmp")
        except Exception as e:
            logger.warning(f"  FMP failed for {ticker}: {e}")
            self._track_failure("fmp")

        # Try yfinance
        try:
            logger.info(f"  Attempting yfinance info for {ticker}")
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            self._track_success("yfinance")
            usage_tracker.increment("yfinance")  # Track API usage
            result = {
                "pe_ratio": info.get('trailingPE') or info.get('forwardPE'),
                "market_cap": info.get('marketCap'),
                "dividend_yield": info.get('dividendYield'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "source": "yfinance"
            }
            # Cache the result
            cache_manager.cache.set(f"fundamentals_{ticker}", result)
            return result
        except Exception as e:
            logger.warning(f"  yfinance info failed for {ticker}: {e}")
            self._track_failure("yfinance")

        # Try cache
        try:
            logger.info(f"  Attempting cache for {ticker}")
            cache_key = f"fundamentals_{ticker}"
            cached_data = cache_manager.cache.get(cache_key, max_age_minutes=10080)  # Allow 7-day old data

            if cached_data:
                self._track_success("cache")
                usage_tracker.increment("cache")  # Track cache usage
                logger.info(f"  Using cached fundamentals for {ticker}")
                return {
                    **cached_data,
                    "source": "cache",
                    "is_stale": True
                }
            self._track_failure("cache")
        except Exception as e:
            logger.warning(f"  Cache failed for {ticker}: {e}")
            self._track_failure("cache")

        logger.error(f"All sources failed for {ticker} fundamentals")
        return None

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """
        Calculate RSI from price series

        Args:
            prices: Pandas Series of closing prices
            period: RSI calculation period (default 14)

        Returns:
            RSI value between 0-100
        """
        try:
            if len(prices) < period + 1:
                return None

            # Calculate price changes
            delta = prices.diff()

            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)

            # Calculate average gain and loss
            avg_gain = gains.rolling(window=period).mean()
            avg_loss = losses.rolling(window=period).mean()

            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1])
        except Exception as e:
            logger.error(f"RSI calculation error: {e}")
            return None

    def _calculate_macd(self, prices: pd.Series) -> Optional[Dict]:
        """
        Calculate MACD from price series

        Args:
            prices: Pandas Series of closing prices

        Returns:
            Dictionary with MACD, signal, and histogram
        """
        try:
            if len(prices) < 26:
                return None

            # Calculate EMAs
            ema12 = prices.ewm(span=12, adjust=False).mean()
            ema26 = prices.ewm(span=26, adjust=False).mean()

            # Calculate MACD line
            macd_line = ema12 - ema26

            # Calculate signal line (9-day EMA of MACD)
            signal_line = macd_line.ewm(span=9, adjust=False).mean()

            # Calculate histogram
            histogram = macd_line - signal_line

            return {
                "macd": float(macd_line.iloc[-1]),
                "macd_signal": float(signal_line.iloc[-1]),
                "macd_histogram": float(histogram.iloc[-1])
            }
        except Exception as e:
            logger.error(f"MACD calculation error: {e}")
            return None

    def get_technical_indicators(self, ticker: str, period: str = "3mo") -> Optional[Dict]:
        """
        Get technical indicators with fallback:
        1. Try Alpha Vantage for RSI/MACD if available
        2. If fails, fetch yfinance history and calculate manually
        3. If fails, try cache

        Returns:
            Dictionary with RSI, MACD, signal, histogram, and source
        """
        logger.info(f"Fetching technical indicators for {ticker}")

        # Try Alpha Vantage first
        try:
            logger.info(f"  Attempting Alpha Vantage for {ticker}")
            if self.alpha_vantage:
                rsi_data = self.alpha_vantage.get_rsi(ticker)
                macd_data = self.alpha_vantage.get_macd(ticker)

                if rsi_data and macd_data:
                    self._track_success("alpha_vantage")
                    usage_tracker.increment("alpha_vantage")  # Track API usage
                    result = {
                        "rsi": rsi_data['rsi'],
                        "macd": macd_data['macd'],
                        "macd_signal": macd_data['signal'],
                        "macd_histogram": macd_data['histogram'],
                        "source": "alpha_vantage"
                    }
                    # Cache the result
                    cache_manager.cache.set(f"technical_{ticker}", result)
                    return result
            self._track_failure("alpha_vantage")
        except Exception as e:
            logger.warning(f"  Alpha Vantage failed for {ticker}: {e}")
            self._track_failure("alpha_vantage")

        # Try yfinance with manual calculation
        try:
            logger.info(f"  Attempting yfinance with manual calculation for {ticker}")
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period=period)

            logger.info(f"  yfinance returned {len(hist)} days of data")

            if not hist.empty and len(hist) >= 14:  # Need at least 14 for RSI
                closes = hist['Close']

                # Calculate RSI
                rsi = self._calculate_rsi(closes, period=14)

                # Calculate MACD (will return None if insufficient data)
                macd_data = self._calculate_macd(closes)

                # Accept partial results - at least RSI
                if rsi is not None:
                    self._track_success("yfinance")
                    usage_tracker.increment("yfinance")  # Track API usage
                    result = {
                        "rsi": rsi,
                        "macd": macd_data['macd'] if macd_data else None,
                        "macd_signal": macd_data['macd_signal'] if macd_data else None,
                        "macd_histogram": macd_data['macd_histogram'] if macd_data else None,
                        "source": "yfinance"
                    }
                    # Cache the result
                    cache_manager.cache.set(f"technical_{ticker}", result)
                    return result
                else:
                    raise ValueError("Failed to calculate RSI from yfinance data")
            else:
                raise ValueError(f"Insufficient data from yfinance: got {len(hist)} days, need at least 14")
        except Exception as e:
            logger.warning(f"  yfinance technical calculation failed for {ticker}: {e}")
            self._track_failure("yfinance")

        # Try cache
        try:
            logger.info(f"  Attempting cache for {ticker}")
            cache_key = f"technical_{ticker}"
            cached_data = cache_manager.cache.get(cache_key, max_age_minutes=1440)  # Allow 24h old data

            if cached_data:
                self._track_success("cache")
                usage_tracker.increment("cache")  # Track cache usage
                logger.info(f"  Using cached technical data for {ticker}")
                return {
                    **cached_data,
                    "source": "cache",
                    "is_stale": True
                }
            self._track_failure("cache")
        except Exception as e:
            logger.warning(f"  Cache failed for {ticker}: {e}")
            self._track_failure("cache")

        logger.error(f"All sources failed for {ticker} technical indicators")
        return None


# Singleton instance
smart_fetcher = SmartDataFetcher()


# Example usage
if __name__ == "__main__":
    # Test the smart fetcher
    fetcher = SmartDataFetcher()

    test_ticker = "AAPL"

    print(f"\n{'='*60}")
    print(f"Testing SmartDataFetcher with {test_ticker}")
    print(f"{'='*60}\n")

    # Test current price
    print("1. Testing get_current_price:")
    price_data = fetcher.get_current_price(test_ticker)
    print(f"   Result: {price_data}\n")

    # Test quote data
    print("2. Testing get_quote_data:")
    quote_data = fetcher.get_quote_data(test_ticker)
    print(f"   Result: {quote_data}\n")

    # Test fundamentals
    print("3. Testing get_fundamentals:")
    fundamentals = fetcher.get_fundamentals(test_ticker)
    print(f"   Result: {fundamentals}\n")

    # Test technical indicators
    print("4. Testing get_technical_indicators:")
    technicals = fetcher.get_technical_indicators(test_ticker)
    print(f"   Result: {technicals}\n")

    # Print usage stats
    print(f"\n{'='*60}")
    print("Usage Statistics:")
    print(f"{'='*60}")
    stats = fetcher.get_usage_stats()
    for source, counts in stats.items():
        total = counts['success'] + counts['failure']
        success_rate = (counts['success'] / total * 100) if total > 0 else 0
        print(f"{source:15} - Success: {counts['success']}, Failure: {counts['failure']}, Rate: {success_rate:.1f}%")
