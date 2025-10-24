# Opportunity Scanner Agent - Backend Implementation

## Overview

The Opportunity Scanner Agent is a sophisticated market screening system that identifies high-potential microcap opportunities based on multiple factors including momentum, technicals, fundamentals, and sector preferences.

## Features

### Screening Criteria
- **Market Cap**: $50M - $2B (true microcap/small-cap range)
- **Sectors**: Technology, Healthcare, Biotechnology, Energy
- **Price Range**: $2.00 - $50.00
- **Volume**: Minimum 100,000 shares/day
- **Technical Filters**:
  - RSI: 25-75 (avoid extreme overbought/oversold)
  - Price Change: 1-25% daily (momentum with volatility control)

### Scoring System (0-100 points) - FIXED & VERIFIED

**Scoring Weights (totals exactly 100):**
```python
SCORING_WEIGHTS = {
    "momentum": 25,      # 25% - Price action, volume, breakouts
    "technical": 25,     # 25% - RSI, MACD, moving averages
    "fundamental": 25,   # 25% - Growth, valuation, cash position
    "sentiment": 10,     # 10% - News sentiment, insider activity
    "sector": 15         # 15% - Preferred sectors bonus
}
```

1. **Momentum Score (0-25 points max)**
   - Price movement today (0-15 points)
   - Volume spike vs. average (0-10 points)
   - **Capped at 25 points**

2. **Technical Score (0-25 points max)**
   - RSI positioning (0-10 points)
   - 52-week high/low position (0-15 points)
   - **Capped at 25 points**

3. **Fundamental Score (0-25 points max)**
   - P/E ratio valuation (0-10 points)
   - Price-to-Book ratio (0-8 points)
   - Revenue growth (0-7 points)
   - **Capped at 25 points**

4. **Sentiment Score (0-10 points max)**
   - *Placeholder for future news sentiment analysis*
   - **Capped at 10 points**

5. **Sector Match (0-15 points max)**
   - Full points if in preferred sectors
   - **Capped at 15 points**

**Safety Features:**
- Each category has explicit cap using `min(score, max_weight)`
- Overflow detection logs error if total > 100
- Initialization verifies weights sum to 100

### Recommendation Levels
- **Strong Buy**: Score ≥ 80
- **Buy**: Score ≥ 70
- **Consider**: Score ≥ 60
- **Watch**: Score ≥ 40

## Implementation

### File Structure
```
agents/
├── __init__.py
└── opportunity_scanner.py
```

### Key Components

#### OpportunityScannerAgent Class
```python
from agents.opportunity_scanner import OpportunityScannerAgent, get_scanner

# Initialize scanner
scanner = OpportunityScannerAgent()

# Run scan
opportunities = scanner.scan_for_opportunities(max_results=10)
```

#### Main Methods

1. **scan_for_opportunities(max_results=10)**
   - Scans ticker universe
   - Applies filters
   - Scores opportunities
   - Returns top N ranked by score

2. **_fetch_ticker_data(ticker)**
   - Uses yfinance to fetch real-time data
   - Calculates technical indicators (RSI)
   - Returns comprehensive ticker data dict

3. **_apply_filters(ticker, data)**
   - Market cap filter
   - Price range filter
   - Volume filter
   - RSI filter
   - Price change filter

4. **_score_opportunity(ticker, data)**
   - Multi-factor scoring
   - Returns (score, signals_breakdown)

5. **_generate_reasoning(ticker, score, signals, data)**
   - Template-based reasoning
   - Highlights key factors

### Return Format
```json
{
    "ticker": "GILT",
    "score": 57,
    "price": 13.72,
    "market_cap": 881794304,
    "sector": "Technology",
    "signals": {
        "momentum": 0,
        "technical": 22,
        "fundamental": 20,
        "sentiment": 0,
        "sector_match": 15
    },
    "recommendation": "Watch",
    "target_price": 14.41,
    "reasoning": "Near 52-week high with RSI at 50. Strong revenue growth (37%). Preferred sector: Technology.",
    "source": "yfinance",
    "scanned_at": "2025-10-21T23:47:04.000000Z"
}
```

## Test Results

### Test Run Output
```
Scanning 40 tickers...
Found 3 opportunities:

1. GILT - Score: 57/100 (Watch)
   - Technology sector
   - Near 52-week high
   - 37% revenue growth

2. RGNX - Score: 46/100 (Watch)
   - Healthcare sector
   - Strong technical setup

3. EDIT - Score: 44/100 (Watch)
   - Healthcare sector
   - Good positioning
```

### Statistics
- **Tickers Scanned**: 40
- **Filtered Out**: 35 (87.5%)
- **Errors**: 2 (delisted stocks)
- **Opportunities Found**: 3
- **Scan Time**: ~20 seconds

## Test Universe

Currently testing with 40 microcap tickers across preferred sectors:

- **Technology**: TSLA, NVDA, AMD, PLTR, SOFI, RIVN, etc.
- **Biotechnology**: NTLA, CRSP, EDIT, BEAM, RGNX, etc.
- **Energy**: UUUU, CCJ, DNN, UEC, SMR, OKLO, etc.
- **Space/Satellite**: CRWV, GSAT, ASTS, LUNR, RKLB, etc.

## Error Handling

✅ **Graceful Failures**
- Skips tickers with fetch errors
- Continues scan if individual ticker fails
- Returns empty list if all sources fail
- Never crashes the scan

✅ **Comprehensive Logging**
- Scan start/end
- Filter pass/fail counts
- Individual ticker scores
- Final opportunity count

## Future Enhancements

### Phase 2
- [ ] News sentiment analysis (0-15 points)
- [ ] AI-generated reasoning (Claude)
- [ ] Dynamic ticker universe (yfinance screeners)
- [ ] Backtesting framework
- [ ] Integration with SmartDataFetcher

### Phase 3
- [ ] Real-time monitoring
- [ ] Alert system for new opportunities
- [ ] Historical tracking
- [ ] Performance analytics

## Testing

Run the test script:
```bash
python test_opportunity_scanner.py
```

This will:
1. Initialize the scanner
2. Scan the test universe
3. Display top 10 opportunities
4. Show detailed signal breakdowns

## API Integration (Next Step)

To integrate with the FastAPI backend, you'll need to:

1. Add endpoint to `api/main.py`:
```python
from agents.opportunity_scanner import get_scanner

@app.get("/api/opportunities")
async def get_opportunities():
    scanner = get_scanner()
    opportunities = scanner.scan_for_opportunities(max_results=10)
    return opportunities
```

2. Update frontend to add "Opportunities" tab
3. Display opportunities in a card grid layout

## Notes

- **Data Source**: Currently using yfinance (free, unlimited)
- **Scan Frequency**: Recommend every 5-15 minutes during market hours
- **Cache Strategy**: Consider caching results for 5 minutes
- **Rate Limiting**: yfinance has no strict limits but respect fair usage

## Performance

- **Scan Speed**: ~0.5 seconds per ticker
- **Memory Usage**: Minimal (processes tickers sequentially)
- **API Calls**: 1 yfinance call per ticker
- **Scalability**: Can handle 100-1000 ticker universe

## Status

✅ **Completed**
- Core scanning logic
- Multi-factor scoring system
- Filter pipeline
- Error handling
- Test suite
- Documentation

🚧 **Pending**
- API endpoint integration
- Frontend dashboard tab
- News sentiment analysis
- Dynamic ticker universe
