# Project Tehama - Deployment Guide

## Railway Deployment

### Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Code pushed to GitHub
3. **API Keys**: Have all API keys ready (see `.env.example`)

### Deployment Steps

#### 1. Connect GitHub to Railway

1. Go to [railway.app](https://railway.app) and log in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your repositories
5. Select the `microcap_agent` repository

#### 2. Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```
ANTHROPIC_API_KEY=<your_key>
ALPACA_API_KEY=<your_key>
ALPACA_SECRET_KEY=<your_key>
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPHA_VANTAGE_API_KEY=<your_key>
FMP_API_KEY=<your_key>
FINNHUB_API_KEY=<your_key>
POLYGON_API_KEY=<your_key>
NEWSAPI_KEY=<your_key>
```

#### 3. Deploy

Railway will automatically:
- Detect `railway.json` configuration
- Install dependencies from `requirements.txt`
- Run `python start_api.py` (as specified in railway.json)
- Expose the service on a public URL

#### 4. Verify Deployment

Once deployed, Railway will provide a URL like:
```
https://project-tehama-production.up.railway.app
```

Test the endpoints:
- `https://your-url.railway.app/health` - Should return `{"status":"healthy"}`
- `https://your-url.railway.app/` - Dashboard UI
- `https://your-url.railway.app/api/portfolio` - Portfolio data
- `https://your-url.railway.app/api/opportunities/latest` - Scanner results

### Features That Work in Production

✅ **Real-time Portfolio Tracking** - Alpaca integration
✅ **AI Recommendations** - Claude analysis
✅ **Opportunity Scanner** - Scheduled scans (8 AM, 10 AM, 12 PM, 2 PM ET)
✅ **Smart Caching** - Market-aware TTL (reduces API calls by 99%)
✅ **yfinance Fallback** - Never hits rate limits
✅ **Dashboard** - React frontend with auto-refresh

### Scheduled Jobs

The scheduler runs automatically in production:
- **8:00 AM ET** - Morning scan
- **10:00 AM ET** - Mid-morning scan
- **12:00 PM ET** - Midday scan
- **2:00 PM ET** - Afternoon scan

Results cached to `opportunities_latest.json` and served via `/api/opportunities/latest`

### Monitoring

Check logs in Railway dashboard:
- **Deployment Logs**: Build and startup logs
- **Application Logs**: Runtime logs, scan results, errors

Look for:
```
✓ Opportunity scanner scheduler started
🔍 opportunity_scanner initialized with 40 tickers in universe
```

### Troubleshooting

**Issue**: 404 errors for API endpoints
- **Fix**: Ensure `railway.json` has correct `startCommand`

**Issue**: Missing environment variables
- **Fix**: Double-check all keys are set in Railway Variables tab

**Issue**: Scheduler not running
- **Fix**: Check application logs for scheduler initialization messages

**Issue**: API rate limits
- **Fix**: Smart caching should prevent this. Check cache hit rate at `/api/cache/stats`

### Cost Estimate

Railway Free Tier: $5/month credit
- **Expected usage**: ~$3-4/month
- **Includes**: 500 hours/month (more than enough)

### Security Notes

🔒 **Never commit**:
- `config.py` (contains API keys)
- `.env` files
- `api_usage.json` (may contain usage data)
- Any `*_latest.json` cache files

✅ **Safe to commit**:
- `.env.example` (template only)
- All source code
- `requirements.txt`
- `railway.json`
- `Procfile`

### Local Development vs Production

| Feature | Local | Production (Railway) |
|---------|-------|---------------------|
| Dashboard URL | `http://localhost:8000` | `https://your-app.railway.app` |
| Caching | File-based | File-based (persistent disk) |
| Scheduler | Runs on startup | Runs 24/7 |
| API Keys | `.env` file | Railway Variables |
| Logs | Terminal | Railway Dashboard |

### Next Steps After Deployment

1. **Bookmark Dashboard URL** - Access from anywhere
2. **Set Alerts** - Railway can notify you of deployment issues
3. **Monitor Usage** - Check `/api/usage` endpoint
4. **Review Scans** - Check `/api/opportunities/latest` for scan results
5. **Customize Scheduler** - Edit `start_api.py` to adjust scan times

### Support

- Railway Docs: https://docs.railway.app
- Project Issues: GitHub Issues tab
- Railway Discord: https://discord.gg/railway
