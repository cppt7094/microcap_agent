"""
API Diagnosis Script - Test all data sources for a specific ticker
"""
import sys
from api_clients import MarketDataManager
import asyncio
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


async def diagnose():
    """Diagnose API calls for all data sources"""
    mgr = MarketDataManager()
    test_ticker = 'AAPL'  # Use liquid ticker for testing

    print(f"\n{'='*60}")
    print(f"DIAGNOSING API CALLS FOR {test_ticker}")
    print(f"{'='*60}\n")

    # Test Alpha Vantage RSI
    print("Testing Alpha Vantage RSI...")
    start = time.time()
    try:
        if mgr.alpha_vantage:
            rsi_data = mgr.alpha_vantage.get_rsi(test_ticker)
            rsi_value = rsi_data.get('rsi') if rsi_data else 'None'
            print(f"✓ SUCCESS: RSI = {rsi_value} ({time.time()-start:.2f}s)")
        else:
            print("✗ SKIPPED: Alpha Vantage not configured")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    time.sleep(13)  # Alpha Vantage rate limit: 5 calls/min = wait 12s between calls

    # Test Alpha Vantage MACD
    print("\nTesting Alpha Vantage MACD...")
    start = time.time()
    try:
        if mgr.alpha_vantage:
            macd_data = mgr.alpha_vantage.get_macd(test_ticker)
            macd_value = macd_data.get('macd') if macd_data else 'None'
            print(f"✓ SUCCESS: MACD = {macd_value} ({time.time()-start:.2f}s)")
        else:
            print("✗ SKIPPED: Alpha Vantage not configured")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test Polygon Snapshot
    print("\nTesting Polygon Snapshot...")
    start = time.time()
    try:
        if mgr.polygon:
            snapshot = mgr.polygon.get_snapshot(test_ticker)
            price = snapshot.get('current_price') if snapshot else 'None'
            print(f"✓ SUCCESS: Price = ${price} ({time.time()-start:.2f}s)")
        else:
            print("✗ SKIPPED: Polygon not configured")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test FMP Profile
    print("\nTesting FMP Profile...")
    start = time.time()
    try:
        if mgr.fmp:
            profile = mgr.fmp.get_company_profile(test_ticker)
            pe_ratio = profile.get('pe_ratio') if profile else 'None'
            print(f"✓ SUCCESS: P/E = {pe_ratio} ({time.time()-start:.2f}s)")
        else:
            print("✗ SKIPPED: FMP not configured")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test Finnhub News
    print("\nTesting Finnhub News...")
    start = time.time()
    try:
        if mgr.finnhub:
            news = mgr.finnhub.get_company_news(test_ticker, days_back=7)
            article_count = len(news) if news else 0
            print(f"✓ SUCCESS: {article_count} articles ({time.time()-start:.2f}s)")
        else:
            print("✗ SKIPPED: Finnhub not configured")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test NewsAPI
    print("\nTesting NewsAPI...")
    start = time.time()
    try:
        if mgr.news_api:
            news = mgr.news_api.get_stock_news(test_ticker, days_back=7)
            article_count = len(news) if news else 0
            print(f"✓ SUCCESS: {article_count} articles ({time.time()-start:.2f}s)")
        else:
            print("✗ SKIPPED: NewsAPI not configured")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test SEC API
    print("\nTesting SEC API...")
    start = time.time()
    try:
        if mgr.sec_api:
            filings = mgr.sec_api.get_recent_filings(test_ticker, days_back=30)
            filing_count = len(filings) if filings else 0
            print(f"✓ SUCCESS: {filing_count} filings ({time.time()-start:.2f}s)")
        else:
            print("✗ SKIPPED: SEC API not configured")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    print(f"\n{'='*60}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*60}\n")


async def test_specific_ticker(ticker: str):
    """Test a specific ticker (like your CRWV)"""
    mgr = MarketDataManager()

    print(f"\n{'='*60}")
    print(f"DETAILED DIAGNOSIS FOR {ticker}")
    print(f"{'='*60}\n")

    # Test comprehensive news (what enhanced report uses)
    print(f"Testing comprehensive news for {ticker}...")
    start = time.time()
    try:
        news_data = await mgr.get_comprehensive_news([ticker])
        ticker_news = news_data.get(ticker, {})

        print(f"✓ News aggregation completed ({time.time()-start:.2f}s)")
        print(f"  Total articles: {ticker_news.get('total_articles', 0)}")
        print(f"  Sentiment: {ticker_news.get('sentiment', {}).get('label', 'UNKNOWN')}")
        print(f"  Sentiment score: {ticker_news.get('sentiment', {}).get('score', 0):.2f}")
        print(f"  Catalyst detected: {ticker_news.get('catalyst_detected', False)}")

        if ticker_news.get('catalysts'):
            print(f"  Catalysts found:")
            for catalyst in ticker_news['catalysts'][:3]:
                print(f"    - {catalyst.get('type')}: {catalyst.get('article_title')}")

    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test insider activity
    print(f"\nTesting insider activity for {ticker}...")
    start = time.time()
    try:
        insider_data = await mgr.get_insider_activity([ticker])
        ticker_insider = insider_data.get(ticker, {})

        print(f"✓ Insider activity completed ({time.time()-start:.2f}s)")
        print(f"  Recent buys: {len(ticker_insider.get('recent_buys', []))}")
        print(f"  Recent sells: {len(ticker_insider.get('recent_sells', []))}")
        print(f"  Signal: {ticker_insider.get('signal', 'UNKNOWN')}")

    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test market regime
    print(f"\nTesting market regime analysis...")
    start = time.time()
    try:
        regime = await mgr.analyze_market_regime()

        print(f"✓ Market regime completed ({time.time()-start:.2f}s)")
        print(f"  Trend: {regime.get('trend', 'UNKNOWN')}")
        print(f"  Volatility: {regime.get('volatility', 'UNKNOWN')}")
        print(f"  Breadth: {regime.get('breadth', 'UNKNOWN')}")
        print(f"  Confidence: {regime.get('confidence', 0):.0%}")

    except Exception as e:
        print(f"✗ FAILED: {e}")

    print(f"\n{'='*60}\n")


async def main():
    """Run all diagnostics"""

    # Basic API tests
    await diagnose()

    # Test your specific ticker
    print("\n" + "="*60)
    choice = input("Test a specific ticker? (y/n): ").lower()

    if choice == 'y':
        ticker = input("Enter ticker symbol (e.g., CRWV): ").upper()
        await test_specific_ticker(ticker)


if __name__ == "__main__":
    asyncio.run(main())
