# Railway Deployment Checklist

## ✅ Pre-Deployment (Complete)

- [x] `railway.json` created - Deployment configuration
- [x] `Procfile` created - Process command
- [x] `.env.example` created - Environment variable template
- [x] `requirements.txt` updated - All dependencies added
- [x] `.gitignore` updated - Sensitive files excluded
- [x] `DEPLOYMENT.md` created - Full deployment guide

## 📋 Ready to Deploy

### Files Created:
```
railway.json      - Railway configuration (229 bytes)
Procfile          - Process command (54 bytes)
.env.example      - Environment template (533 bytes)
DEPLOYMENT.md     - Deployment guide (4.2K)
requirements.txt  - Updated with APScheduler, pytz, requests
.gitignore        - Updated to exclude cache files
```

### What Railway Will Do:

1. **Detect Configuration**
   - Reads `railway.json` for build/deploy settings
   - Uses `Procfile` if railway.json doesn't specify command
   
2. **Install Dependencies**
   - Runs `pip install -r requirements.txt`
   - Installs: FastAPI, Uvicorn, Anthropic, Alpaca, yfinance, pandas, APScheduler, etc.
   
3. **Start Application**
   - Executes: `python start_api.py`
   - Exposes on Railway's provided PORT
   - Health check on `/health` endpoint

4. **Provide Public URL**
   - Format: `https://project-name-production.up.railway.app`
   - Automatically handles HTTPS/SSL
   - Domain mapping available (optional)

### Environment Variables Needed in Railway:

Copy these from your local `.env` or `config.py`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
ALPACA_API_KEY=AK...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPHA_VANTAGE_API_KEY=...
FMP_API_KEY=...
FINNHUB_API_KEY=...
POLYGON_API_KEY=...
NEWSAPI_KEY=...
```

**Important**: Don't commit these! Only add them in Railway's Variables tab.

## 🚀 Deployment Steps

### 1. Push to GitHub (if not already done)

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Deploy on Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Go to **Variables** tab
6. Add all environment variables (see list above)
7. Deploy!

### 3. Verify Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app.railway.app/health

# Dashboard (open in browser)
https://your-app.railway.app/

# Portfolio data
curl https://your-app.railway.app/api/portfolio

# Opportunities scanner
curl https://your-app.railway.app/api/opportunities/latest
```

### 4. Check Logs

In Railway dashboard:
- **Deployment** tab: Build logs
- **Deployments** → Click latest → View logs

Look for success messages:
```
✓ Opportunity scanner scheduler started
🔍 opportunity_scanner initialized with 40 tickers in universe
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## 📊 What Works in Production

✅ **Real-time Portfolio** - Live Alpaca data
✅ **AI Recommendations** - Claude analysis via Anthropic API
✅ **Opportunity Scanner** - Scheduled scans at 8 AM, 10 AM, 12 PM, 2 PM ET
✅ **Smart Caching** - Market-aware TTL (60s market hours, 5min after hours)
✅ **Dashboard** - React UI with auto-refresh
✅ **API Endpoints** - 8+ working REST endpoints

## 🎯 Post-Deployment

1. **Bookmark URL** - Access dashboard from anywhere
2. **Monitor First Scan** - Check logs around 8 AM ET
3. **Test Endpoints** - Verify all API routes work
4. **Check Usage** - Visit `/api/usage` to see API consumption

## 🔧 Troubleshooting

### Build Fails
- Check Railway logs for missing dependencies
- Verify `requirements.txt` has all packages
- Ensure Python version compatibility (3.9+)

### Application Crashes
- Check for missing environment variables
- Verify API keys are correct
- Look for ImportError in logs

### Scheduler Not Running
- Check logs for "scheduler started" message
- Verify APScheduler and pytz are installed
- Check timezone configuration (should be US/Eastern)

### 404 Errors
- Verify `start_api.py` is running correctly
- Check CORS settings if calling from external domain
- Ensure frontend files are in `frontend/` directory

## 💰 Cost

**Railway Free Tier**: $5/month credit
- Expected usage: ~$3-4/month
- Includes: 500 hours/month runtime
- Free outbound bandwidth: 100GB/month

**Upgrade if needed**: $20/month for unlimited hours

## 📝 Notes

- **Scheduler runs 24/7** - Scans happen even when you're offline
- **Logs persist** - Check Railway dashboard for historical logs
- **Auto-redeploy** - Push to GitHub triggers automatic deployment
- **Environment**: Production (use `ALPACA_BASE_URL=https://api.alpaca.markets` for live trading)

## ✨ You're Ready!

All deployment files are configured. Follow DEPLOYMENT.md for detailed step-by-step instructions.

**Next**: Push to GitHub and deploy on Railway! 🚀
