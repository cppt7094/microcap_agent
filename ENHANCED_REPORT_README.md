# Enhanced Report Generator - Multi-Source Market Intelligence

A comprehensive AI-powered market intelligence system that aggregates data from 6+ sources to generate actionable morning briefs and portfolio analysis.

## 🎯 Overview

The Enhanced Report Generator leverages your existing Project Tehama infrastructure to create institutional-grade market intelligence reports by combining:

- **Alpha Vantage**: Technical indicators (RSI, MACD, SMA)
- **Polygon**: Real-time quotes, VIX, unusual volume detection
- **FMP (Financial Modeling Prep)**: Fundamentals, sector performance
- **Finnhub**: Company news, social sentiment
- **NewsAPI**: News aggregation and sentiment analysis
- **SEC API**: Insider trading activity (Form 4 filings)
- **Alpaca**: Live portfolio positions and P&L

All powered by **Claude AI** for intelligent analysis and actionable insights.

---

## 🚀 Quick Start

### 1. Basic Usage

Run a full morning brief with all data sources:

```bash
python run_enhanced_report.py
```

This will:
- Gather data from all 6+ sources
- Analyze each portfolio position with AI
- Scan for high-probability setups
- Generate comprehensive markdown report
- Save to `reports/morning_brief_YYYYMMDD_HHMMSS.md`

### 2. Quick Market Check

Get a fast market regime assessment:

```bash
python run_enhanced_report.py --quick
```

Output:
```
📊 Market Regime:
   Trend: BULLISH (SPY SMA20 vs SMA50)
   Volatility: NORMAL (VIX: 16.5)
   Breadth: STRONG (73% sectors positive)
   Confidence: 85%

✅ FAVORABLE CONDITIONS - Consider long positions
```

### 3. Test Components

Verify all data sources are working:

```bash
python run_enhanced_report.py --test
```

### 4. Scheduled Execution

Run automatically at 8:30 AM ET every weekday (pre-market):

```bash
python run_enhanced_report.py --schedule
```

---

## 📊 Report Structure

The generated morning brief includes:

### 1. Executive Summary (AI-Generated)
- Today's key action items
- Market context
- Biggest opportunities/risks

### 2. Market Intelligence
- **Multi-Source Regime Analysis**
  - Trend (Alpha Vantage SMA)
  - Volatility (Polygon VIX)
  - Breadth (FMP sector data)
  - Futures (Finnhub)

- **Sector Performance** (FMP)
- **Unusual Activity** (Polygon volume scanner)

### 3. Portfolio Analysis
- Total value and daily P&L
- **Position Intelligence** (AI analysis per position using ALL data sources)
- **Insider Activity** (SEC Form 4 filings)

### 4. High-Probability Setups
- Top 5 opportunities scored using:
  - Volume (Polygon)
  - Technical signals (Alpha Vantage)
  - News sentiment (NewsAPI + Finnhub)
  - Insider activity (SEC)

### 5. News Catalysts
- Finnhub institutional news
- NewsAPI sentiment analysis
- Catalyst detection (earnings, FDA, partnerships, etc.)

### 6. Action Plan (AI-Generated)
- Prioritized action items
- Position management recommendations
- Entry/exit levels where applicable

---

## 🔧 Architecture

### Core Components

#### 1. EnhancedReportGenerator
Main class that orchestrates data gathering and report generation.

```python
from enhanced_report_generator import EnhancedReportGenerator

report_gen = EnhancedReportGenerator(
    market_service=market_service,
    portfolio_service=portfolio_service
)

report = await report_gen.generate_morning_brief()
```

#### 2. MarketServiceAdapter
Adapts your existing `MarketDataManager` to work with async report generator.

Key methods:
- `analyze_market_regime()` - Multi-source regime analysis
- `scan_unusual_activity()` - Polygon volume scanner
- `get_comprehensive_news()` - Aggregated news + sentiment
- `get_insider_activity()` - SEC Form 4 parsing

#### 3. PortfolioServiceAdapter
Adapts Alpaca API to provide portfolio data.

---

## 📚 API Methods Reference

### Market Data Methods

#### `analyze_market_regime()`
Combines SPY technicals, VIX, and sector breadth into regime analysis.

**Returns:**
```python
{
    'trend': 'BULLISH' | 'BEARISH',
    'volatility': 'HIGH' | 'NORMAL',
    'volatility_value': 16.5,  # VIX value
    'breadth': 'STRONG' | 'NEUTRAL' | 'WEAK',
    'breadth_ratio': 0.73,  # 73% sectors positive
    'confidence': 0.85,  # 85% confidence
    'spy_price': 580.50,
    'spy_sma20': 575.25,
    'spy_sma50': 570.10
}
```

#### `scan_unusual_activity()`
Scans for stocks with unusual volume (>1M shares).

**Returns:**
```python
[
    {
        'symbol': 'TSLA',
        'volume': 125_000_000,
        'price': 245.50,
        'change_pct': 8.5,
        'unusual_flag': 'HIGH_VOLUME'
    },
    ...
]
```

#### `get_comprehensive_news(tickers: List[str])`
Aggregates news from multiple sources with sentiment analysis.

**Returns:**
```python
{
    'AAPL': {
        'articles': [...],  # Top 10 articles
        'total_articles': 45,
        'sentiment': {
            'score': 0.65,  # -1 to 1
            'label': 'POSITIVE',
            'positive_count': 25,
            'negative_count': 10
        },
        'catalyst_detected': True,
        'catalysts': [
            {
                'type': 'earnings',
                'article_title': 'Apple beats Q4 estimates',
                'url': '...',
                'published': '2025-10-17T08:00:00Z'
            }
        ],
        'social_sentiment': {
            'bullish_pct': 65,
            'bearish_pct': 35
        }
    }
}
```

#### `get_insider_activity(tickers: List[str])`
Tracks insider buying/selling from SEC Form 4 filings.

**Returns:**
```python
{
    'NVDA': {
        'recent_buys': [
            {
                'filed_at': '2025-10-15',
                'description': 'Purchase by CEO',
                'link': 'https://...'
            }
        ],
        'recent_sells': [...],
        'net_activity': 2,  # More buys than sells
        'total_form4_filings': 5,
        'signal': 'BULLISH'
    }
}
```

---

## 🎨 Customization

### Adding Custom Scanners

Add your own opportunity scanners:

```python
# In enhanced_report_generator.py
async def _scan_opportunities(self) -> List[Dict]:
    opportunities = []

    # Your custom scanner
    custom_scan = await self.market.your_custom_scanner()
    opportunities.extend(custom_scan)

    # Score and rank
    for opp in opportunities:
        opp['score'] = await self._score_opportunity(opp)

    return sorted(opportunities, key=lambda x: x['score'], reverse=True)[:5]
```

### Customizing Scoring

Modify `_score_opportunity()` to change how setups are ranked:

```python
async def _score_opportunity(self, opportunity: Dict) -> float:
    score = 0.0

    # Volume score (30%)
    if opportunity['volume'] > 5_000_000:
        score += 0.3

    # Your custom scoring logic
    if opportunity.get('your_metric') > threshold:
        score += 0.2

    return min(score, 1.0)
```

### Adding Data Sources

Extend `MarketServiceAdapter` to add new data sources:

```python
class MarketServiceAdapter:
    async def get_your_new_data_source(self):
        # Implement your data source
        return await self.mgr.your_new_api_call()
```

---

## 📝 Example Output

```markdown
# 📊 INTELLIGENT MORNING BRIEF - Project Tehama
**Friday, October 17, 2025**
**Data Sources: Alpha Vantage | Finnhub | FMP | Polygon | SEC | News API**

## 🎯 EXECUTIVE SUMMARY
Portfolio up 2.3% ($1,250) with strong breadth across holdings. Market regime
is BULLISH with NORMAL volatility - favorable conditions for swing trades. Three
high-conviction setups identified with positive insider activity and technical
confirmation. Key action: Consider adding to APLD on dip to $36.50 support.

## 📈 MARKET INTELLIGENCE
### Multi-Source Regime Analysis
**Trend**: BULLISH (Alpha Vantage SMA Analysis)
**Volatility**: NORMAL (Polygon VIX: 16.5)
**Breadth**: STRONG (FMP Advance/Decline)
**Futures**: SPY +0.45% | NQ +0.75% (Finnhub)

### Sector Performance (FMP)
🟢 **Technology**: +1.25%
🟢 **Healthcare**: +0.85%
🟢 **Consumer Discretionary**: +0.65%
🔴 **Energy**: -0.45%
🔴 **Utilities**: -0.25%

### Unusual Activity (Polygon)
- **SOUN**: 15,245,000 vol, +12.5% change
- **APLD**: 8,950,000 vol, +8.2% change
- **NTLA**: 5,680,000 vol, +6.8% change

## 💼 PORTFOLIO ANALYSIS
**Total Value**: $54,250.00
**Day P/L**: +$1,250.00 (+2.36%)

### Position Intelligence

#### APLD
Strong momentum continuing with heavy institutional buying. RSI at 68 suggests
room before overbought. Support at $36.50, resistance at $42.00. Consider
adding on pullback to $37 range with tight stop at $35.

#### NTLA
Bullish MACD crossover confirmed. Recent insider buying (3 Form 4s filed)
adds conviction. News catalyst detected: FDA approval timeline update.
Hold current position, watch for break above $28 for potential add.

...

## 🎯 HIGH-PROBABILITY SETUPS

**1. RGTI** (Score: 87%)
   Volume: 25,500,000 | Change: +15.2%
   - Unusual volume + bullish insider signal + positive news sentiment

**2. SOUN** (Score: 82%)
   Volume: 15,245,000 | Change: +12.5%
   - Technical breakout + partnership catalyst detected

...

## ⚡ ACTION PLAN
1. **APLD** - Set alert at $36.50 for potential add (2-3 shares)
2. **NTLA** - Hold current position, trail stop to $24
3. **RGTI** - Watch for entry on pullback to $2.15-$2.20 range
4. **Review** - CRWV position if breaks below $135 support
5. **Monitor** - Overall portfolio risk at 85% deployed, keep 15% cash reserve

---
*Generated using: 6 data sources | 7 positions analyzed*
*Next update: After market open*
```

---

## 🔒 Security & API Keys

Ensure these environment variables or Config settings are set:

```python
ANTHROPIC_API_KEY       # Claude AI
ALPACA_API_KEY          # Portfolio data
ALPACA_SECRET_KEY
ALPHA_VANTAGE_KEY       # Technicals
POLYGON_API_KEY         # Real-time data, VIX
FMP_API_KEY             # Fundamentals
FINNHUB_KEY             # News
NEWS_API_KEY            # News aggregation
SEC_API_KEY             # Insider activity
```

---

## 📊 Performance Metrics

The report generator tracks:
- Data sources queried
- Positions analyzed
- Opportunities scored
- API tokens used (Claude)
- Generation time

Example:
```
✓ Report generated successfully!
   - 6 data sources queried
   - 7 positions analyzed with AI
   - 45 opportunities scanned, 5 high-conviction
   - Claude tokens: 1,250 input / 850 output
   - Generation time: 12.5 seconds
```

---

## 🐛 Troubleshooting

### Issue: "No market data available"
**Solution**: Check API keys in `config.py` are valid

### Issue: "Rate limit exceeded"
**Solution**:
- Alpha Vantage: Max 5 calls/minute (free tier)
- Polygon: Max 5 calls/minute (free tier)
- Consider upgrading API plans or adding delays

### Issue: "Claude API timeout"
**Solution**: Reduce number of positions being analyzed or increase timeout

### Issue: "SEC API returns empty data"
**Solution**: Not all tickers have recent Form 4 filings - this is expected

---

## 🔄 Integration with Existing Workflow

### Add to Morning Brief
Integrate with your existing `morning_brief.py`:

```python
from enhanced_report_generator import EnhancedReportGenerator

async def run_morning_brief(dry_run=False, send_email=False):
    # Your existing code...

    # Add enhanced report
    enhanced_report = await report_gen.generate_morning_brief()

    # Optionally email it
    if send_email:
        email_system.send_enhanced_report(enhanced_report)
```

### Add to Continuous Monitor
Integrate with `continuous_monitor.py`:

```python
# Run enhanced analysis at key times
if current_time.hour == 8 and current_time.minute == 30:
    # Pre-market enhanced brief
    await run_enhanced_morning_brief()
elif current_time.hour == 16 and current_time.minute == 0:
    # Market close summary with enhanced analysis
    await generate_enhanced_close_summary()
```

---

## 📈 Future Enhancements

Planned features:
- [ ] Options flow analysis (Polygon options data)
- [ ] Short interest tracking
- [ ] Earnings calendar integration
- [ ] Backtesting framework for opportunity scoring
- [ ] Real-time WebSocket feeds for intraday updates
- [ ] PDF report generation with charts
- [ ] Mobile push notifications for critical alerts

---

## 📄 License

Part of Project Tehama - Personal use only

---

## 🙏 Credits

Built on top of:
- Anthropic Claude AI
- Alpha Vantage API
- Polygon.io
- Financial Modeling Prep
- Finnhub
- NewsAPI
- SEC API
- Alpaca Markets

---

**Questions or issues?** Check the troubleshooting section or review the example scripts in this repository.
