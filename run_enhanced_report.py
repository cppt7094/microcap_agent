"""
Example script to run the Enhanced Report Generator with your existing infrastructure
"""
import asyncio
import os
import sys
from datetime import datetime
import alpaca_trade_api as tradeapi
from config import Config
from api_clients import MarketDataManager
from enhanced_report_generator import (
    EnhancedReportGenerator,
    PortfolioServiceAdapter,
    MarketServiceAdapter
)

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


async def run_enhanced_morning_brief():
    """
    Generate the enhanced morning brief using all your existing data sources
    """
    print("🚀 Starting Enhanced Morning Brief Generation...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Initialize your EXISTING services
        print("📊 Initializing data services...")

        # Alpaca API for portfolio data
        alpaca = tradeapi.REST(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )

        # Your existing MarketDataManager
        market_data_mgr = MarketDataManager()

        # Create adapters to make them work with the report generator
        portfolio_service = PortfolioServiceAdapter(alpaca)
        market_service = MarketServiceAdapter(market_data_mgr)

        print("✓ Services initialized\n")

        # Create the enhanced report generator
        print("🤖 Initializing Enhanced Report Generator...")
        report_gen = EnhancedReportGenerator(
            market_service=market_service,
            portfolio_service=portfolio_service
        )
        print("✓ Report generator ready\n")

        # Generate the comprehensive morning brief
        print("📈 Gathering data from 6+ sources...")
        print("   - Alpha Vantage (SPY, technicals)")
        print("   - Polygon (VIX, unusual volume)")
        print("   - FMP (fundamentals, sectors)")
        print("   - Finnhub (news, sentiment)")
        print("   - NewsAPI (news aggregation)")
        print("   - SEC API (insider activity)")
        print("   - Alpaca (portfolio positions)\n")

        report = await report_gen.generate_morning_brief()

        print("✓ Report generated successfully!\n")

        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"morning_brief_{timestamp}.md"
        filepath = os.path.join('reports', filename)

        # Create reports directory if it doesn't exist
        os.makedirs('reports', exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"💾 Report saved to: {filepath}\n")

        # Also print to console
        print("="*80)
        print(report)
        print("="*80)

        return report

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_individual_components():
    """
    Test individual components to verify data sources are working
    """
    print("\n🧪 Testing Individual Data Sources...\n")

    try:
        market_data_mgr = MarketDataManager()

        # Test 1: Market Regime Analysis
        print("1️⃣ Testing Market Regime Analysis...")
        regime = await market_data_mgr.analyze_market_regime()
        print(f"   Trend: {regime.get('trend')}")
        print(f"   Volatility: {regime.get('volatility')}")
        print(f"   Breadth: {regime.get('breadth')}")
        print(f"   Confidence: {regime.get('confidence', 0):.0%}")
        print("   ✓ Market regime analysis working\n")

        # Test 2: Unusual Activity Scan
        print("2️⃣ Testing Unusual Activity Scanner...")
        unusual = await market_data_mgr.scan_unusual_activity()
        print(f"   Found {len(unusual)} stocks with unusual volume")
        if unusual:
            top = unusual[0]
            print(f"   Top: {top.get('symbol')} - {top.get('volume'):,.0f} shares")
        print("   ✓ Unusual activity scanner working\n")

        # Test 3: Comprehensive News
        print("3️⃣ Testing Comprehensive News Aggregation...")
        test_tickers = ['AAPL', 'TSLA']
        news = await market_data_mgr.get_comprehensive_news(test_tickers)
        for ticker in test_tickers:
            ticker_news = news.get(ticker, {})
            article_count = ticker_news.get('total_articles', 0)
            sentiment = ticker_news.get('sentiment', {}).get('label', 'UNKNOWN')
            print(f"   {ticker}: {article_count} articles, sentiment: {sentiment}")
        print("   ✓ News aggregation working\n")

        # Test 4: Insider Activity
        print("4️⃣ Testing Insider Activity Tracker...")
        insiders = await market_data_mgr.get_insider_activity(test_tickers)
        for ticker in test_tickers:
            insider_data = insiders.get(ticker, {})
            buys = len(insider_data.get('recent_buys', []))
            sells = len(insider_data.get('recent_sells', []))
            signal = insider_data.get('signal', 'UNKNOWN')
            print(f"   {ticker}: {buys} buys, {sells} sells - Signal: {signal}")
        print("   ✓ Insider activity tracker working\n")

        print("✅ All components tested successfully!")

    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()


async def quick_market_check():
    """
    Quick market regime check (fast alternative to full report)
    """
    print("\n⚡ Quick Market Check...\n")

    try:
        market_data_mgr = MarketDataManager()
        regime = await market_data_mgr.analyze_market_regime()

        print(f"📊 Market Regime:")
        print(f"   Trend: {regime.get('trend')} (SPY SMA20 vs SMA50)")
        print(f"   Volatility: {regime.get('volatility')} (VIX: {regime.get('volatility_value', 0):.1f})")
        print(f"   Breadth: {regime.get('breadth')} ({regime.get('breadth_ratio', 0):.0%} sectors positive)")
        print(f"   Confidence: {regime.get('confidence', 0):.0%}")

        # Trading recommendation
        if regime.get('trend') == 'BULLISH' and regime.get('volatility') == 'NORMAL':
            print("\n✅ FAVORABLE CONDITIONS - Consider long positions")
        elif regime.get('trend') == 'BEARISH' and regime.get('volatility') == 'HIGH':
            print("\n⚠️  UNFAVORABLE CONDITIONS - Reduce exposure, defensive mode")
        else:
            print("\n⚪ MIXED CONDITIONS - Selective positioning, manage risk carefully")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Enhanced Report Generator - Multi-source market intelligence',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_enhanced_report.py                    # Generate full morning brief
  python run_enhanced_report.py --test             # Test individual components
  python run_enhanced_report.py --quick            # Quick market regime check
  python run_enhanced_report.py --schedule         # Run on schedule (pre-market)
        """
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test individual data source components'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick market regime check only'
    )

    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run on schedule (8:30 AM pre-market)'
    )

    args = parser.parse_args()

    if args.test:
        # Test mode
        asyncio.run(test_individual_components())
    elif args.quick:
        # Quick check mode
        asyncio.run(quick_market_check())
    elif args.schedule:
        # Scheduled mode
        from apscheduler.schedulers.blocking import BlockingScheduler

        scheduler = BlockingScheduler()

        # Run at 8:30 AM ET every weekday (pre-market)
        scheduler.add_job(
            lambda: asyncio.run(run_enhanced_morning_brief()),
            'cron',
            day_of_week='mon-fri',
            hour=8,
            minute=30,
            timezone='America/New_York'
        )

        print("📅 Scheduler started - will run at 8:30 AM ET on weekdays")
        print("Press Ctrl+C to stop\n")

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\n👋 Scheduler stopped")
    else:
        # Default: Run full report now
        asyncio.run(run_enhanced_morning_brief())


if __name__ == "__main__":
    main()
