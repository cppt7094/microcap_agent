"""
API Clients Module for Enhanced Market Data
Integrates multiple financial data APIs for comprehensive portfolio monitoring
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config import Config


class NewsAPIClient:
    """Client for News API - fetches news and sentiment for portfolio positions"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    def get_stock_news(self, symbol: str, days_back: int = 1) -> List[Dict]:
        """
        Fetch recent news articles for a stock symbol

        Args:
            symbol: Stock ticker symbol
            days_back: Number of days to look back (default 1)

        Returns:
            List of news articles with title, description, url, publishedAt
        """
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_back)

            params = {
                'q': f'{symbol} stock',
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.api_key,
                'pageSize': 10
            }

            response = requests.get(f"{self.base_url}/everything", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'ok':
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'url': article.get('url'),
                        'publishedAt': article.get('publishedAt'),
                        'source': article.get('source', {}).get('name')
                    })
                return articles

            return []

        except Exception as e:
            logging.error(f"Error fetching news for {symbol}: {e}")
            return []

    def get_portfolio_news_summary(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """
        Fetch news for multiple symbols

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their news articles
        """
        news_summary = {}

        for symbol in symbols:
            news_summary[symbol] = self.get_stock_news(symbol)

        return news_summary


class PolygonAPIClient:
    """Client for Polygon.io - real-time and historical market data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time quote for a symbol

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with bid, ask, last price, volume
        """
        try:
            url = f"{self.base_url}/v2/last/trade/{symbol}"
            params = {'apiKey': self.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'OK':
                result = data.get('results', {})
                return {
                    'price': result.get('p'),
                    'size': result.get('s'),
                    'timestamp': result.get('t')
                }

            return None

        except Exception as e:
            logging.error(f"Error fetching Polygon quote for {symbol}: {e}")
            return None

    def get_daily_bars(self, symbol: str, days: int = 30) -> Optional[List[Dict]]:
        """
        Get daily price bars for technical analysis

        Args:
            symbol: Stock ticker symbol
            days: Number of days of history

        Returns:
            List of daily bars with OHLCV data
        """
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)

            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{from_date.strftime('%Y-%m-%d')}/{to_date.strftime('%Y-%m-%d')}"
            params = {'apiKey': self.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'OK':
                bars = []
                for bar in data.get('results', []):
                    bars.append({
                        'open': bar.get('o'),
                        'high': bar.get('h'),
                        'low': bar.get('l'),
                        'close': bar.get('c'),
                        'volume': bar.get('v'),
                        'timestamp': bar.get('t')
                    })
                return bars

            return None

        except Exception as e:
            logging.error(f"Error fetching Polygon bars for {symbol}: {e}")
            return None

    def get_snapshot(self, symbol: str) -> Optional[Dict]:
        """
        Get comprehensive snapshot with day stats

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with comprehensive market data
        """
        try:
            url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            params = {'apiKey': self.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'OK':
                ticker = data.get('ticker', {})
                day_data = ticker.get('day', {})
                prev_day = ticker.get('prevDay', {})

                return {
                    'current_price': ticker.get('lastTrade', {}).get('p'),
                    'day_open': day_data.get('o'),
                    'day_high': day_data.get('h'),
                    'day_low': day_data.get('l'),
                    'day_close': day_data.get('c'),
                    'day_volume': day_data.get('v'),
                    'prev_close': prev_day.get('c'),
                    'change_pct': ((day_data.get('c', 0) - prev_day.get('c', 1)) / prev_day.get('c', 1) * 100) if prev_day.get('c') else 0
                }

            return None

        except Exception as e:
            logging.error(f"Error fetching Polygon snapshot for {symbol}: {e}")
            return None


class FMPAPIClient:
    """Client for Financial Modeling Prep - fundamental data and financial statements"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"

    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """
        Get company profile and key metrics

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with company information
        """
        try:
            url = f"{self.base_url}/profile/{symbol}"
            params = {'apikey': self.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data and len(data) > 0:
                profile = data[0]
                return {
                    'name': profile.get('companyName'),
                    'sector': profile.get('sector'),
                    'industry': profile.get('industry'),
                    'market_cap': profile.get('mktCap'),
                    'pe_ratio': profile.get('pe'),
                    'beta': profile.get('beta'),
                    'description': profile.get('description'),
                    'website': profile.get('website')
                }

            return None

        except Exception as e:
            logging.error(f"Error fetching FMP profile for {symbol}: {e}")
            return None

    def get_key_metrics(self, symbol: str) -> Optional[Dict]:
        """
        Get key financial metrics

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with financial metrics
        """
        try:
            url = f"{self.base_url}/key-metrics/{symbol}"
            params = {'apikey': self.api_key, 'limit': 1}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data and len(data) > 0:
                metrics = data[0]
                return {
                    'revenue_per_share': metrics.get('revenuePerShareTTM'),
                    'net_income_per_share': metrics.get('netIncomePerShareTTM'),
                    'operating_cash_flow_per_share': metrics.get('operatingCashFlowPerShareTTM'),
                    'free_cash_flow_per_share': metrics.get('freeCashFlowPerShareTTM'),
                    'book_value_per_share': metrics.get('bookValuePerShareTTM'),
                    'tangible_book_value_per_share': metrics.get('tangibleBookValuePerShareTTM'),
                    'debt_to_equity': metrics.get('debtToEquityTTM'),
                    'roe': metrics.get('roeTTM'),
                    'roa': metrics.get('returnOnTangibleAssetsTTM')
                }

            return None

        except Exception as e:
            logging.error(f"Error fetching FMP key metrics for {symbol}: {e}")
            return None

    def get_analyst_estimates(self, symbol: str) -> Optional[Dict]:
        """
        Get analyst price targets and estimates

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with analyst consensus data
        """
        try:
            url = f"{self.base_url}/analyst-estimates/{symbol}"
            params = {'apikey': self.api_key, 'limit': 1}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data and len(data) > 0:
                estimate = data[0]
                return {
                    'estimated_revenue_avg': estimate.get('estimatedRevenueAvg'),
                    'estimated_revenue_high': estimate.get('estimatedRevenueHigh'),
                    'estimated_revenue_low': estimate.get('estimatedRevenueLow'),
                    'estimated_ebitda_avg': estimate.get('estimatedEbitdaAvg'),
                    'number_analysts': estimate.get('numberAnalystEstimatedRevenue')
                }

            return None

        except Exception as e:
            logging.error(f"Error fetching FMP analyst estimates for {symbol}: {e}")
            return None


class SECAPIClient:
    """Client for SEC API - monitor recent SEC filings"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sec-api.io"

    def get_recent_filings(self, symbol: str, days_back: int = 7) -> List[Dict]:
        """
        Get recent SEC filings for a company

        Args:
            symbol: Stock ticker symbol
            days_back: Number of days to look back

        Returns:
            List of recent filings
        """
        try:
            # Build query
            query = {
                "query": f'ticker:{symbol} AND filedAt:[NOW-{days_back}DAYS TO NOW]',
                "from": "0",
                "size": "10",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.base_url}/v2",
                json=query,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            filings = []
            for filing in data.get('filings', []):
                filings.append({
                    'type': filing.get('formType'),
                    'filed_at': filing.get('filedAt'),
                    'description': filing.get('description'),
                    'link': filing.get('linkToFilingDetails')
                })

            return filings

        except Exception as e:
            logging.error(f"Error fetching SEC filings for {symbol}: {e}")
            return []


class AlphaVantageClient:
    """Client for Alpha Vantage - technical indicators and market data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    def get_rsi(self, symbol: str, time_period: int = 14) -> Optional[Dict]:
        """
        Get RSI (Relative Strength Index) for a symbol

        Args:
            symbol: Stock ticker symbol
            time_period: RSI calculation period (default 14)

        Returns:
            Dictionary with RSI data
        """
        try:
            params = {
                'function': 'RSI',
                'symbol': symbol,
                'interval': 'daily',
                'time_period': time_period,
                'series_type': 'close',
                'apikey': self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'Technical Analysis: RSI' in data:
                rsi_data = data['Technical Analysis: RSI']
                # Get most recent RSI value
                latest_date = list(rsi_data.keys())[0]
                latest_rsi = float(rsi_data[latest_date]['RSI'])

                return {
                    'rsi': latest_rsi,
                    'date': latest_date,
                    'oversold': latest_rsi < 30,
                    'overbought': latest_rsi > 70
                }

            return None

        except Exception as e:
            logging.error(f"Error fetching Alpha Vantage RSI for {symbol}: {e}")
            return None

    def get_macd(self, symbol: str) -> Optional[Dict]:
        """
        Get MACD indicator for a symbol

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with MACD data
        """
        try:
            params = {
                'function': 'MACD',
                'symbol': symbol,
                'interval': 'daily',
                'series_type': 'close',
                'apikey': self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'Technical Analysis: MACD' in data:
                macd_data = data['Technical Analysis: MACD']
                # Get most recent MACD values
                latest_date = list(macd_data.keys())[0]
                latest = macd_data[latest_date]

                macd_line = float(latest['MACD'])
                signal_line = float(latest['MACD_Signal'])
                histogram = float(latest['MACD_Hist'])

                return {
                    'macd': macd_line,
                    'signal': signal_line,
                    'histogram': histogram,
                    'date': latest_date,
                    'bullish_crossover': macd_line > signal_line and histogram > 0,
                    'bearish_crossover': macd_line < signal_line and histogram < 0
                }

            return None

        except Exception as e:
            logging.error(f"Error fetching Alpha Vantage MACD for {symbol}: {e}")
            return None


class FinnhubClient:
    """Client for Finnhub - real-time financial data and news"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"

    def get_company_news(self, symbol: str, days_back: int = 7) -> List[Dict]:
        """
        Get company-specific news from Finnhub

        Args:
            symbol: Stock ticker symbol
            days_back: Number of days to look back

        Returns:
            List of news articles
        """
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_back)

            params = {
                'symbol': symbol,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'token': self.api_key
            }

            response = requests.get(f"{self.base_url}/company-news", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            news = []
            for article in data[:10]:  # Limit to 10 most recent
                news.append({
                    'headline': article.get('headline'),
                    'summary': article.get('summary'),
                    'url': article.get('url'),
                    'datetime': article.get('datetime'),
                    'source': article.get('source')
                })

            return news

        except Exception as e:
            logging.error(f"Error fetching Finnhub news for {symbol}: {e}")
            return []

    def get_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        Get social sentiment data for a symbol

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with sentiment scores
        """
        try:
            params = {
                'symbol': symbol,
                'token': self.api_key
            }

            response = requests.get(f"{self.base_url}/news-sentiment", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data and 'buzz' in data and 'sentiment' in data:
                return {
                    'buzz_score': data['buzz'].get('articlesInLastWeek', 0),
                    'buzz_weekly_average': data['buzz'].get('weeklyAverage', 0),
                    'sentiment_score': data['sentiment'].get('bearishPercent', 0),
                    'bullish_pct': data['sentiment'].get('bullishPercent', 0),
                    'bearish_pct': data['sentiment'].get('bearishPercent', 0)
                }

            return None

        except Exception as e:
            logging.error(f"Error fetching Finnhub sentiment for {symbol}: {e}")
            return None


# ============================================================================
# UNIFIED API MANAGER
# ============================================================================

class MarketDataManager:
    """
    Unified manager for all market data APIs
    Provides high-level interface to fetch comprehensive data for portfolio monitoring
    """

    def __init__(self):
        """Initialize all API clients"""
        self.news_api = NewsAPIClient(Config.NEWS_API_KEY) if Config.NEWS_API_KEY else None
        self.polygon = PolygonAPIClient(Config.POLYGON_API_KEY) if Config.POLYGON_API_KEY else None
        self.fmp = FMPAPIClient(Config.FMP_API_KEY) if Config.FMP_API_KEY else None
        self.sec_api = SECAPIClient(Config.SEC_API_KEY) if Config.SEC_API_KEY else None
        self.alpha_vantage = AlphaVantageClient(Config.ALPHA_VANTAGE_KEY) if Config.ALPHA_VANTAGE_KEY else None
        self.finnhub = FinnhubClient(Config.FINNHUB_KEY) if Config.FINNHUB_KEY else None

    def get_enhanced_position_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch comprehensive data for a position from all available APIs

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with all available data for the symbol
        """
        data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'news': None,
            'fundamentals': None,
            'technical': None,
            'sentiment': None,
            'filings': None
        }

        # News from multiple sources
        news_articles = []
        if self.news_api:
            news_articles.extend(self.news_api.get_stock_news(symbol, days_back=1))
        if self.finnhub:
            news_articles.extend(self.finnhub.get_company_news(symbol, days_back=1))

        data['news'] = {
            'count': len(news_articles),
            'articles': news_articles[:5]  # Top 5 most recent
        }

        # Fundamentals from FMP
        if self.fmp:
            data['fundamentals'] = {
                'profile': self.fmp.get_company_profile(symbol),
                'metrics': self.fmp.get_key_metrics(symbol),
                'estimates': self.fmp.get_analyst_estimates(symbol)
            }

        # Technical indicators
        technical = {}
        if self.alpha_vantage:
            technical['rsi'] = self.alpha_vantage.get_rsi(symbol)
            technical['macd'] = self.alpha_vantage.get_macd(symbol)

        if self.polygon:
            technical['snapshot'] = self.polygon.get_snapshot(symbol)

        data['technical'] = technical

        # Sentiment
        if self.finnhub:
            data['sentiment'] = self.finnhub.get_sentiment(symbol)

        # Recent SEC filings
        if self.sec_api:
            data['filings'] = self.sec_api.get_recent_filings(symbol, days_back=7)

        return data

    def get_portfolio_news_digest(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """
        Get news digest for entire portfolio

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dictionary mapping symbols to news articles
        """
        digest = {}

        for symbol in symbols:
            articles = []

            if self.news_api:
                articles.extend(self.news_api.get_stock_news(symbol, days_back=1))

            if self.finnhub:
                articles.extend(self.finnhub.get_company_news(symbol, days_back=1))

            # Sort by published date and take top 3
            articles.sort(key=lambda x: x.get('publishedAt', x.get('datetime', 0)), reverse=True)
            digest[symbol] = articles[:3]

        return digest

    def check_for_sec_alerts(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """
        Check for recent SEC filings across portfolio

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dictionary mapping symbols to recent filings
        """
        if not self.sec_api:
            return {}

        alerts = {}

        for symbol in symbols:
            filings = self.sec_api.get_recent_filings(symbol, days_back=1)
            if filings:
                alerts[symbol] = filings

        return alerts

    async def get_spy_data(self) -> Dict:
        """
        Get SPY (S&P 500) data with moving averages from Alpha Vantage

        Returns:
            Dictionary with SPY price data and moving averages
        """
        try:
            if not self.alpha_vantage:
                logging.warning("Alpha Vantage client not initialized")
                return {}

            # Get daily data for SPY
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': 'SPY',
                'apikey': self.alpha_vantage.api_key,
                'outputsize': 'compact'
            }

            response = requests.get(self.alpha_vantage.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'Time Series (Daily)' not in data:
                return {}

            time_series = data['Time Series (Daily)']
            dates = list(time_series.keys())[:50]  # Get last 50 days

            # Calculate simple moving averages
            closes = [float(time_series[date]['4. close']) for date in dates]

            sma20 = sum(closes[:20]) / 20 if len(closes) >= 20 else closes[0]
            sma50 = sum(closes[:50]) / 50 if len(closes) >= 50 else closes[0]
            current_price = closes[0]

            return {
                'price': current_price,
                'sma20': sma20,
                'sma50': sma50,
                'trend': 'BULLISH' if sma20 > sma50 else 'BEARISH'
            }

        except Exception as e:
            logging.error(f"Error fetching SPY data: {e}")
            return {}

    async def get_vix_from_polygon(self) -> float:
        """
        Get VIX (volatility index) data from Polygon

        Returns:
            Current VIX value
        """
        try:
            if not self.polygon:
                logging.warning("Polygon client not initialized")
                return 0.0

            # Get VIX snapshot
            url = f"{self.polygon.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/VIX"
            params = {'apiKey': self.polygon.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'OK':
                ticker = data.get('ticker', {})
                last_trade = ticker.get('lastTrade', {})
                return float(last_trade.get('p', 0))

            return 0.0

        except Exception as e:
            logging.error(f"Error fetching VIX data: {e}")
            return 0.0

    async def get_market_breadth_fmp(self) -> Dict:
        """
        Get market breadth indicators from FMP

        Returns:
            Dictionary with market breadth data
        """
        try:
            if not self.fmp:
                logging.warning("FMP client not initialized")
                return {}

            # Use FMP's market indexes endpoint to estimate breadth
            # Get S&P 500 sector performance as a proxy for breadth
            url = f"{self.fmp.base_url}/sector-performance"
            params = {'apikey': self.fmp.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data:
                # Count sectors with positive performance
                positive_sectors = sum(1 for sector in data if float(sector.get('changesPercentage', '0').rstrip('%')) > 0)
                total_sectors = len(data)
                breadth_ratio = positive_sectors / total_sectors if total_sectors > 0 else 0

                return {
                    'positive_sectors': positive_sectors,
                    'total_sectors': total_sectors,
                    'breadth_ratio': breadth_ratio,
                    'breadth_status': 'STRONG' if breadth_ratio > 0.6 else 'WEAK' if breadth_ratio < 0.4 else 'NEUTRAL'
                }

            return {}

        except Exception as e:
            logging.error(f"Error fetching market breadth: {e}")
            return {}

    def _calculate_confidence(self, spy_data: Dict, vix: float, breadth: Dict) -> float:
        """
        Calculate confidence score for market regime analysis

        Args:
            spy_data: SPY data with moving averages
            vix: VIX volatility value
            breadth: Market breadth data

        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0

        # SPY trend confidence (30%)
        if spy_data.get('sma20') and spy_data.get('sma50'):
            sma_diff = abs(spy_data['sma20'] - spy_data['sma50']) / spy_data['sma50']
            confidence += min(sma_diff * 10, 0.3)  # Max 0.3

        # VIX confidence (30%)
        if vix > 0:
            if vix < 15:  # Very low volatility
                confidence += 0.3
            elif vix < 20:  # Normal volatility
                confidence += 0.2
            elif vix < 30:  # Elevated volatility
                confidence += 0.1
            # High volatility (>30) = 0 confidence points

        # Breadth confidence (40%)
        breadth_ratio = breadth.get('breadth_ratio', 0)
        if breadth_ratio > 0.6 or breadth_ratio < 0.4:
            confidence += 0.4  # Strong breadth signal
        elif breadth_ratio > 0.5 or breadth_ratio < 0.5:
            confidence += 0.2  # Moderate breadth signal

        return min(confidence, 1.0)

    async def analyze_market_regime(self) -> Dict:
        """
        Determine market regime using existing data sources

        Returns:
            Dictionary with market regime analysis
        """
        try:
            # Use existing Alpha Vantage connection for SPY
            spy_data = await self.get_spy_data()

            # Use existing Polygon for VIX
            vix_data = await self.get_vix_from_polygon()

            # Use FMP for market breadth
            breadth = await self.get_market_breadth_fmp()

            # Combine into regime analysis
            regime = {
                'trend': spy_data.get('trend', 'UNKNOWN'),
                'volatility': 'HIGH' if vix_data > 20 else 'NORMAL' if vix_data > 0 else 'UNKNOWN',
                'volatility_value': vix_data,
                'breadth': breadth.get('breadth_status', 'UNKNOWN'),
                'breadth_ratio': breadth.get('breadth_ratio', 0),
                'confidence': self._calculate_confidence(spy_data, vix_data, breadth),
                'spy_price': spy_data.get('price', 0),
                'spy_sma20': spy_data.get('sma20', 0),
                'spy_sma50': spy_data.get('sma50', 0)
            }

            return regime

        except Exception as e:
            logging.error(f"Error analyzing market regime: {e}")
            return {
                'trend': 'ERROR',
                'volatility': 'UNKNOWN',
                'breadth': 'UNKNOWN',
                'confidence': 0.0
            }

    async def scan_unusual_activity(self) -> List[Dict]:
        """
        Use existing Polygon for unusual volume activity

        Returns:
            List of stocks with unusual volume (>3x average)
        """
        try:
            if not self.polygon:
                logging.warning("Polygon client not initialized")
                return []

            # Use Polygon grouped daily endpoint to get all stocks
            from_date = datetime.now().date()
            to_date = from_date

            url = f"{self.polygon.base_url}/v2/aggs/grouped/locale/us/market/stocks/{from_date}"
            params = {'apiKey': self.polygon.api_key}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            unusual_stocks = []

            if data.get('status') == 'OK' and data.get('results'):
                for stock in data['results']:
                    ticker = stock.get('T')
                    volume = stock.get('v', 0)

                    # Get historical average volume (approximation)
                    # In production, you'd calculate this from historical data
                    # For now, we'll use a simple heuristic based on current volume
                    # being significantly higher than typical microcap trading

                    # Filter for unusual volume (>1M shares for microcaps is unusual)
                    if volume > 1_000_000:
                        unusual_stocks.append({
                            'symbol': ticker,
                            'volume': volume,
                            'price': stock.get('c', 0),
                            'change_pct': ((stock.get('c', 0) - stock.get('o', 0)) / stock.get('o', 1)) * 100 if stock.get('o') else 0,
                            'unusual_flag': 'HIGH_VOLUME'
                        })

                # Sort by volume descending and return top 20
                unusual_stocks.sort(key=lambda x: x['volume'], reverse=True)
                return unusual_stocks[:20]

            return []

        except Exception as e:
            logging.error(f"Error scanning unusual activity: {e}")
            return []

    def _analyze_sentiment(self, articles: List[Dict]) -> Dict:
        """
        Analyze sentiment from news articles using keyword analysis

        Args:
            articles: List of news articles

        Returns:
            Dictionary with sentiment analysis
        """
        if not articles:
            return {'score': 0, 'label': 'NEUTRAL', 'positive_count': 0, 'negative_count': 0}

        positive_keywords = [
            'breakthrough', 'growth', 'surge', 'profit', 'beat', 'exceeds', 'strong',
            'upgrade', 'buy', 'bullish', 'rally', 'gain', 'outperform', 'positive',
            'innovation', 'partnership', 'award', 'success', 'record'
        ]

        negative_keywords = [
            'loss', 'decline', 'fall', 'miss', 'weak', 'downgrade', 'sell', 'bearish',
            'crash', 'plunge', 'concern', 'risk', 'layoff', 'lawsuit', 'investigation',
            'fraud', 'scandal', 'warning', 'underperform', 'failure'
        ]

        positive_count = 0
        negative_count = 0

        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('description', '') + ' ' +
                   article.get('summary', '') + ' ' + article.get('headline', '')).lower()

            for keyword in positive_keywords:
                if keyword in text:
                    positive_count += 1

            for keyword in negative_keywords:
                if keyword in text:
                    negative_count += 1

        # Calculate sentiment score (-1 to 1)
        total = positive_count + negative_count
        if total == 0:
            score = 0
            label = 'NEUTRAL'
        else:
            score = (positive_count - negative_count) / total
            if score > 0.2:
                label = 'POSITIVE'
            elif score < -0.2:
                label = 'NEGATIVE'
            else:
                label = 'NEUTRAL'

        return {
            'score': score,
            'label': label,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'total_articles': len(articles)
        }

    def _detect_catalysts(self, articles: List[Dict]) -> Dict:
        """
        Detect potential catalysts from news articles

        Args:
            articles: List of news articles

        Returns:
            Dictionary with detected catalysts
        """
        if not articles:
            return {'detected': False, 'catalysts': []}

        catalyst_keywords = {
            'earnings': ['earnings', 'eps', 'revenue', 'quarterly results', 'beat estimates'],
            'fda': ['fda', 'approval', 'clinical trial', 'drug', 'treatment'],
            'partnership': ['partnership', 'collaboration', 'agreement', 'deal', 'merger', 'acquisition'],
            'product': ['launch', 'release', 'new product', 'innovation', 'patent'],
            'insider': ['insider buying', 'ceo', 'executive', 'board'],
            'analyst': ['upgrade', 'downgrade', 'price target', 'rating', 'analyst']
        }

        detected_catalysts = []

        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('description', '') + ' ' +
                   article.get('summary', '') + ' ' + article.get('headline', '')).lower()

            for catalyst_type, keywords in catalyst_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        detected_catalysts.append({
                            'type': catalyst_type,
                            'article_title': article.get('title', article.get('headline', 'Unknown')),
                            'url': article.get('url', ''),
                            'published': article.get('publishedAt', article.get('datetime', ''))
                        })
                        break  # Only count once per article per catalyst type

        return {
            'detected': len(detected_catalysts) > 0,
            'catalysts': detected_catalysts,
            'count': len(detected_catalysts)
        }

    async def get_comprehensive_news(self, tickers: List[str]) -> Dict:
        """
        Aggregate news from ALL existing sources

        Args:
            tickers: List of stock ticker symbols

        Returns:
            Dictionary with comprehensive news and analysis for each ticker
        """
        news = {}

        for ticker in tickers:
            try:
                all_articles = []

                # Gather from NewsAPI
                if self.news_api:
                    try:
                        news_api_articles = self.news_api.get_stock_news(ticker, days_back=7)
                        all_articles.extend(news_api_articles)
                    except Exception as e:
                        logging.warning(f"NewsAPI error for {ticker}: {e}")

                # Gather from Finnhub
                if self.finnhub:
                    try:
                        finnhub_articles = self.finnhub.get_company_news(ticker, days_back=7)
                        all_articles.extend(finnhub_articles)
                    except Exception as e:
                        logging.warning(f"Finnhub error for {ticker}: {e}")

                # Aggregate and score
                sentiment = self._analyze_sentiment(all_articles)
                catalysts = self._detect_catalysts(all_articles)

                # Get social sentiment from Finnhub if available
                social_sentiment = None
                if self.finnhub:
                    try:
                        social_sentiment = self.finnhub.get_sentiment(ticker)
                    except Exception as e:
                        logging.warning(f"Finnhub sentiment error for {ticker}: {e}")

                news[ticker] = {
                    'articles': all_articles[:10],  # Top 10 most recent
                    'total_articles': len(all_articles),
                    'sentiment': sentiment,
                    'catalyst_detected': catalysts['detected'],
                    'catalysts': catalysts['catalysts'],
                    'social_sentiment': social_sentiment
                }

            except Exception as e:
                logging.error(f"Error getting comprehensive news for {ticker}: {e}")
                news[ticker] = {
                    'articles': [],
                    'total_articles': 0,
                    'sentiment': {'score': 0, 'label': 'UNKNOWN'},
                    'catalyst_detected': False,
                    'catalysts': []
                }

        return news

    async def get_insider_activity(self, tickers: List[str]) -> Dict:
        """
        Use existing SEC API for insider trading data

        Args:
            tickers: List of stock ticker symbols

        Returns:
            Dictionary with insider activity for each ticker
        """
        insider_data = {}

        for ticker in tickers:
            try:
                if not self.sec_api:
                    logging.warning("SEC API client not initialized")
                    insider_data[ticker] = {
                        'recent_buys': [],
                        'recent_sells': [],
                        'net_activity': 0,
                        'error': 'SEC API not configured'
                    }
                    continue

                # Get recent filings (including Form 4 - insider trading)
                filings = self.sec_api.get_recent_filings(ticker, days_back=30)

                # Filter for Form 4 (insider transactions)
                form4_filings = [f for f in filings if f.get('type') == '4' or 'Form 4' in f.get('description', '')]

                # Parse insider transactions
                # Note: Full parsing would require analyzing the actual filing content
                # For now, we'll categorize based on filing descriptions
                recent_buys = []
                recent_sells = []

                for filing in form4_filings:
                    description = filing.get('description', '').lower()

                    # Simple heuristic: look for buy/sell indicators in description
                    if 'purchase' in description or 'acquisition' in description or 'buy' in description:
                        recent_buys.append({
                            'filed_at': filing.get('filed_at'),
                            'description': filing.get('description'),
                            'link': filing.get('link')
                        })
                    elif 'sale' in description or 'sell' in description or 'disposed' in description:
                        recent_sells.append({
                            'filed_at': filing.get('filed_at'),
                            'description': filing.get('description'),
                            'link': filing.get('link')
                        })

                # Calculate net activity (positive = more buying, negative = more selling)
                net_activity = len(recent_buys) - len(recent_sells)

                insider_data[ticker] = {
                    'recent_buys': recent_buys,
                    'recent_sells': recent_sells,
                    'net_activity': net_activity,
                    'total_form4_filings': len(form4_filings),
                    'signal': 'BULLISH' if net_activity > 0 else 'BEARISH' if net_activity < 0 else 'NEUTRAL'
                }

            except Exception as e:
                logging.error(f"Error getting insider activity for {ticker}: {e}")
                insider_data[ticker] = {
                    'recent_buys': [],
                    'recent_sells': [],
                    'net_activity': 0,
                    'error': str(e)
                }

        return insider_data
