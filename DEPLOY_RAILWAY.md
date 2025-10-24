# Deploy to Railway - Quick Guide

## What You're Deploying

A **production-ready multi-agent trading system** with:
- 4 analyst agents (Technical, Fundamental, Sentiment, Risk)
- Meta-Agent with anti-groupthink penalty
- Risk Committee for position sizing
- Opportunity Scanner
- Real-time dashboard
- Smart caching + API fallbacks

---

## Step 1: Push to GitHub ✅ DONE

```bash
git add .
git commit -m "Production ready: Complete multi-agent system"
git push origin main
```

Your repo: https://github.com/cppt7094/microcap_agent

---

## Step 2: Deploy to Railway (5 minutes)

### 2.1 Go to Railway
https://railway.app/new

### 2.2 Deploy from GitHub
1. Click "Deploy from GitHub repo"
2. Select `cppt7094/microcap_agent`
3. Railway auto-detects Python

### 2.3 Add Environment Variables

Click **"Variables"** → **"Raw Editor"** → Paste:

```
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
ALPACA_API_KEY=AKXXXXXXXXXXXXXXX
ALPACA_SECRET_KEY=YOUR_SECRET_KEY
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPHA_VANTAGE_API_KEY=YOUR_KEY
FMP_API_KEY=YOUR_KEY
FINNHUB_API_KEY=YOUR_KEY
NEWSAPI_KEY=YOUR_KEY
PORT=8000
```

### 2.4 Set Start Command

Railway should auto-detect from `Procfile`:
```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

If not, set it manually in **Settings** → **Deploy** → **Start Command**

---

## Step 3: Verify Deployment

### 3.1 Check Railway Logs

Click **"Deployments"** → Latest deployment → **"View Logs"**

Look for:
```
✓ Analyst team initialized (Technical, Fundamental, Sentiment, Risk)
✓ Risk Committee initialized
✓ Meta-Agent initialized
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 3.2 Test Health Endpoint

Railway gives you a URL like: `https://microcap-agent-production.up.railway.app`

Test:
```bash
curl https://YOUR-APP.up.railway.app/health
```

Should return:
```json
{"status": "healthy"}
```

### 3.3 Test Multi-Agent Analysis

```bash
curl "https://YOUR-APP.up.railway.app/api/recommendations/analyze/APLD?apply_risk=true"
```

Should return full analyst breakdown with 4 agents + Meta-Agent + Risk Committee.

---

## Step 4: Monitor API Usage

### Check Usage Stats
```bash
curl https://YOUR-APP.up.railway.app/api/usage
```

Response shows:
```json
{
  "apis": {
    "fmp": {
      "calls": 14,
      "limit": 250,
      "percent": 5.6,
      "status": "ok"
    },
    "alpaca": {
      "calls": 4,
      "limit": 12000,
      "percent": 0.0,
      "status": "ok"
    }
  },
  "cache": {
    "hit_rate": 0.75
  }
}
```

---

## What's Running

### API Endpoints Available:

```
GET /                                    - Dashboard UI
GET /health                              - Health check
GET /api/portfolio                       - Portfolio summary
GET /api/recommendations                 - Cached recommendations
GET /api/recommendations/analyze/{ticker} - Live multi-agent analysis
GET /api/opportunities/scan              - Opportunity scanner
GET /api/opportunities/latest            - Cached opportunities
GET /api/alerts                          - Trading alerts
GET /api/agents/status                   - Agent health
GET /api/usage                           - API usage stats
GET /api/cache/stats                     - Cache performance
```

### Analyst Pipeline:

Every `/api/recommendations/analyze/{ticker}` call:
1. Runs 4 agents (Technical, Fundamental, Sentiment, Risk)
2. Aggregates with Meta-Agent (diversity penalty)
3. Optionally debates with Risk Committee (`?apply_risk=true`)
4. Returns consensus recommendation

---

## Cost Estimates

### Railway Free Tier:
- $5/month credit
- Should cover API hosting
- Sleeps after inactivity (wakes in ~10s)

### API Usage per Analysis:
- **Claude API**: 4 calls (Technical, Fundamental, Sentiment, Risk)
- **FMP**: ~8 calls (fundamentals for ticker + portfolio positions)
- **Alpaca**: 2 calls (price data)
- **yfinance**: 1 call (technical indicators) - FREE

### Daily Costs (100 analyses/day):
- Claude: ~400 calls × $0.003 = **$1.20/day**
- FMP: ~800 calls / 250 limit = **3.2 days worth**
- Total: ~$40/month

---

## Troubleshooting

### Issue: "Analyst team not available"

**Fix**: Check logs for import errors. Verify all files pushed to GitHub.

### Issue: "Claude API error"

**Fix**: Check `ANTHROPIC_API_KEY` in Railway environment variables.

### Issue: High API usage

**Solution 1**: Increase cache TTL
```python
# In api/cache_manager.py
DEFAULT_TTL = 300  # 5 minutes → 600 (10 minutes)
```

**Solution 2**: Use cached endpoints
```
GET /api/opportunities/latest  # Uses cache
GET /api/recommendations        # Uses cache
```

### Issue: Slow response times

**Normal** - First analysis takes 5-10 seconds:
- 4 agents run sequentially
- Each makes API calls
- Claude API adds ~1-2s per agent

**Solution**: Use cache for repeated queries

---

## Scaling Options

### Railway Pro Plan ($20/month):
- No sleep mode
- More resources
- Custom domains

### Optimizations:
1. **Parallel agent execution** (future)
   - Run 4 agents concurrently
   - Reduce total time to ~2-3 seconds

2. **Pre-compute recommendations**
   - Run scanner nightly
   - Cache results
   - API serves from cache

3. **Batch processing**
   - Analyze multiple tickers in one request
   - Amortize Claude API overhead

---

## Security Checklist

✅ Environment variables in Railway (not in code)
✅ `.env` in `.gitignore`
✅ API keys encrypted at rest (Railway)
✅ HTTPS enabled by default (Railway)
✅ CORS configured for localhost only

### Optional: Add API Authentication

Add to `api/main.py`:
```python
from fastapi import Header, HTTPException

async def verify_token(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")

@app.get("/api/recommendations/analyze/{ticker}", dependencies=[Depends(verify_token)])
async def analyze_ticker(ticker: str):
    ...
```

Then add to Railway:
```
API_SECRET_KEY=your_secret_key_here
```

---

## Monitoring

### Railway Dashboard:
- **CPU/Memory**: Check for spikes
- **Response Time**: Should be <5s for analysis
- **Error Rate**: Should be <1%

### Custom Alerts (future):
```python
# In api/services.py
if error_rate > 0.05:
    send_email("High error rate detected")
```

---

## Next Steps After Deployment

1. **Test live endpoints** with real portfolio
2. **Monitor API usage** for first week
3. **Optimize cache TTL** based on usage patterns
4. **Add authentication** if exposing publicly
5. **Set up uptime monitoring** (UptimeRobot)

---

## Support

**Railway Docs**: https://docs.railway.app
**Project GitHub**: https://github.com/cppt7094/microcap_agent
**System Docs**: See `ANALYST_TEAM_SUMMARY.md`

---

## Your Deployment URL

After deploying, Railway gives you:
```
https://microcap-agent-production-XXXX.up.railway.app
```

**Save this URL** - it's your live API endpoint.

Test:
```bash
curl https://YOUR-URL.up.railway.app/health
```

If you see `{"status": "healthy"}`, you're live! 🚀
