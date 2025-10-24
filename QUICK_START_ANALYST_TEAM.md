# Analyst Team - Quick Start Guide

## What You Built

A **4-agent analyst team** that votes on every trade with **groupthink detection** and **automated position sizing**.

```
Technical + Fundamental + Sentiment + Risk
    ↓
Meta-Agent (detects groupthink)
    ↓
Risk Committee (debates position size)
    ↓
Final Recommendation
```

---

## Quick Test

### Test Full Pipeline
```bash
python test_analyst_pipeline.py
```

### Analyze Any Ticker via API
```bash
# Start API server
python start_api.py

# In another terminal:
curl "http://localhost:8000/api/recommendations/analyze/APLD?apply_risk=true"
```

---

## Example Output

```
Technical:   SELL (60%) - MACD bearish
Fundamental: HOLD (30%) - Insufficient data
Sentiment:   HOLD (25%) - No news data
Risk:        SELL (85%) - 50% tech exposure too high

Meta-Agent: SELL (50% confidence) - Healthy diversity

Risk Committee:
  Risk-Seeking: 4 shares
  Risk-Neutral: 3 shares (WINNER)
  Risk-Conservative: 3 shares

Final: SELL 3 shares @ $30.50 stop loss
```

---

## Key Features

### 1. Meta-Agent Diversity Penalty

**Problem**: When all agents agree, it's often a red flag (groupthink)

**Solution**: Penalize extreme consensus
- All agents agree (>80%) → Reduce confidence 15%
- No agents agree (<40%) → Reduce confidence 10%
- Healthy debate (40-80%) → No penalty

### 2. Risk Committee Position Sizing

**Problem**: How many shares to buy/sell?

**Solution**: 3 risk managers debate
- Risk-Seeking: Aggressive (30% position)
- Risk-Neutral: Standard (20% position)
- Risk-Conservative: Cautious (15% position)

Claude API moderates and determines consensus.

### 3. Brutally Honest Agents

All agents use `core_directives.py` for anti-sycophancy:
- Say "INSUFFICIENT DATA" when data is missing
- No hedging language ("might", "could", "possibly")
- Direct actionable advice
- Low confidence when uncertain

---

## API Endpoints

### Analyze Specific Ticker

```bash
GET /api/recommendations/analyze/{ticker}?apply_risk=true

Example:
curl "http://localhost:8000/api/recommendations/analyze/APLD?apply_risk=true"
```

**Response:**
```json
{
  "ticker": "APLD",
  "action": "SELL",
  "confidence": 0.50,
  "qty": 3,
  "reasoning": "Meta-Agent: Moderate consensus for SELL...\n\n[Risk Committee] 3 shares consensus, stop $30.50",
  "agents": ["technical", "fundamental", "sentiment", "risk"],
  "status": "pending"
}
```

---

## Testing Individual Agents

Each agent has a test script:

```bash
# Technical Agent
python -m agents.technical_agent

# Fundamental Agent
python -m agents.fundamental_agent

# Sentiment Agent
python -m agents.sentiment_agent

# Risk Agent
python -m agents.risk_agent

# Meta-Agent
python -m agents.meta_agent

# Risk Committee
python -m agents.risk_committee
```

---

## Agent Roles

| Agent | Focuses On | Data Sources | Confidence Driver |
|-------|------------|--------------|-------------------|
| **Technical** | Price action, RSI, MACD | Polygon, yfinance | Chart patterns, momentum |
| **Fundamental** | P/E, market cap, valuation | FMP API | Business quality, financials |
| **Sentiment** | News, price momentum | Price proxy (future: NewsAPI) | Sentiment trends |
| **Risk** | Portfolio concentration | Portfolio context | Diversification, sector exposure |

---

## When to Use What

### `/api/recommendations` (existing endpoint)
- Returns **hardcoded sample recommendations**
- Fast, no API calls
- Good for testing UI

### `/api/recommendations/analyze/{ticker}` (NEW)
- Runs **live 4-agent analysis**
- Slower (5-10 seconds)
- Real data from APIs
- Use when you want actual analysis

---

## Common Issues

### Issue: "Analyst team not available"

**Fix**: Check imports in `api/services.py`
```bash
# Should see this on startup:
"Analyst team initialized (Technical, Fundamental, Sentiment, Risk)"
```

### Issue: "Claude API error"

**Fix**: Check Anthropic API key in `config.py`
```python
ANTHROPIC_API_KEY = "sk-ant-..."
```

### Issue: "Insufficient data" from agents

**Normal behavior** - agents are brutally honest:
- If no P/E data → "INSUFFICIENT DATA"
- If no news → "No sentiment data available"
- This is intentional (no fake confidence)

---

## Next Steps

### 1. Add Real News Sentiment
Integrate NewsAPI to replace price-based sentiment proxy

### 2. Track Agent Accuracy
Log which agent was right/wrong on each trade

### 3. Optimize Agent Weights
Use historical win rates to weight agents differently

### 4. Add More Agents
- Insider trading agent
- Options flow agent
- Macro/regime agent

---

## Files to Know

**Agent Implementations:**
- `agents/technical_agent.py`
- `agents/fundamental_agent.py`
- `agents/sentiment_agent.py`
- `agents/risk_agent.py`

**Aggregation:**
- `agents/meta_agent.py` - Diversity penalty
- `agents/risk_committee.py` - Position sizing

**Integration:**
- `api/services.py` - `_generate_multi_agent_recommendation()`
- `api/main.py` - `/api/recommendations/analyze/{ticker}`

**Testing:**
- `test_analyst_pipeline.py` - Full pipeline test

**Documentation:**
- `ANALYST_TEAM_SUMMARY.md` - Detailed overview
- `QUICK_START_ANALYST_TEAM.md` - This file

---

## Bottom Line

You now have a **multi-agent trading system** that:
1. Runs 4 specialized agents on every ticker
2. Detects groupthink and penalizes extreme consensus
3. Debates position sizing with Risk Committee
4. Provides transparent, brutally honest analysis

**Test it:**
```bash
curl "http://localhost:8000/api/recommendations/analyze/APLD?apply_risk=true"
```
