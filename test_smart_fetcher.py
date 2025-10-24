"""
Comprehensive test of SmartDataFetcher
"""
from api.data_fetcher import smart_fetcher

print('='*60)
print('SmartDataFetcher Comprehensive Test')
print('='*60)

ticker = 'NVDA'

print(f'\n1. Current Price for {ticker}:')
price = smart_fetcher.get_current_price(ticker)
if price:
    print(f'   Price: ${price["price"]:.2f}')
    print(f'   Source: {price["source"]}')
    print(f'   Stale: {price["is_stale"]}')

print(f'\n2. Quote Data for {ticker}:')
quote = smart_fetcher.get_quote_data(ticker)
if quote:
    print(f'   Open: ${quote["open"]:.2f}, Close: ${quote["close"]:.2f}')
    print(f'   Volume: {quote["volume"]:,}')
    print(f'   Source: {quote["source"]}')

print(f'\n3. Fundamentals for {ticker}:')
fund = smart_fetcher.get_fundamentals(ticker)
if fund:
    if fund.get('pe_ratio'):
        print(f'   PE Ratio: {fund["pe_ratio"]:.2f}')
    if fund.get('market_cap'):
        print(f'   Market Cap: ${fund["market_cap"]/1e9:.2f}B')
    print(f'   Sector: {fund.get("sector", "N/A")}')
    print(f'   Source: {fund["source"]}')

print(f'\n4. Technical Indicators for {ticker}:')
tech = smart_fetcher.get_technical_indicators(ticker)
if tech:
    print(f'   RSI: {tech["rsi"]:.2f}')
    if tech.get('macd'):
        print(f'   MACD: {tech["macd"]:.4f}')
        print(f'   Signal: {tech["macd_signal"]:.4f}')
    print(f'   Source: {tech["source"]}')

print('\n' + '='*60)
print('Final Usage Statistics:')
print('='*60)
stats = smart_fetcher.get_usage_stats()
for source, counts in stats.items():
    total = counts['success'] + counts['failure']
    if total > 0:
        success_rate = (counts['success'] / total * 100)
        check = 'OK' if counts['success'] > 0 else 'X'
        print(f'{source:15} - [{check}] Success: {counts["success"]} | Failure: {counts["failure"]} | {success_rate:.0f}%')
