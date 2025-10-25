# Railway Deployment Troubleshooting Guide

## Common Issues and Fixes

### Issue 1: Application Crashes on Startup

**Symptoms:**
- Build succeeds but app crashes immediately
- Railway logs show "Application error" or no output

**Debugging Steps:**

1. **Check Railway deployment logs** - Click "Deployments" → Latest → "View Logs"

2. **Look for the error stage:**
   - If it fails during import: Missing dependency or import error
   - If it fails after "Importing FastAPI app": Issue in api/main.py initialization
   - If it fails with file write error: Need to use /tmp directory

3. **Deploy minimal version first:**
   ```
   # In Railway, temporarily change Procfile to:
   web: python start_api_minimal.py
   ```
   Then redeploy. If this works, the issue is in the main application code.

---

### Issue 2: File Write Errors (Read-Only Filesystem)

**Error message:**
```
PermissionError: [Errno 30] Read-only file system: 'opportunities_latest.json'
```

**Fix:**
Railway's filesystem is read-only except `/tmp`. We've added `utils/data_paths.py` to handle this.

**Verify the fix:**
- Check that `RAILWAY_ENVIRONMENT=production` is set in Railway Variables
- The app should automatically use `/tmp/` for data files

---

### Issue 3: Missing Environment Variables

**Symptoms:**
- API calls fail with "401 Unauthorized"
- Logs show "API key not found"

**Fix:**
Go to Railway → Your Service → Variables → Raw Editor

Paste the contents of your local `RAILWAY_ENV_VARS.txt` file.

**Required variables:**
```
ANTHROPIC_API_KEY=sk-ant-api03-...
ALPACA_API_KEY=AK...
ALPACA_SECRET_KEY=SZ...
ALPACA_BASE_URL=https://api.alpaca.markets
FMP_API_KEY=...
PORT=8000
RAILWAY_ENVIRONMENT=production
```

---

### Issue 4: Port Binding Error

**Error message:**
```
OSError: [Errno 98] Address already in use
```

**Fix:**
Railway automatically sets the `PORT` environment variable. Ensure `start_api.py` uses it:

```python
port = int(os.getenv("PORT", 8000))
```

This is already implemented in the updated `start_api.py`.

---

### Issue 5: Import Errors

**Error message:**
```
ModuleNotFoundError: No module named 'anthropic'
```

**Fix:**
Check `requirements.txt` includes all dependencies:
```
anthropic>=0.39.0
fastapi>=0.115.6
uvicorn[standard]>=0.34.0
alpaca-trade-api>=3.0.2
yfinance>=0.2.48
requests>=2.32.0
python-dotenv>=1.0.1
pytz>=2024.1
```

Railway automatically installs from `requirements.txt` during build.

---

### Issue 6: Redis Connection Failing

**Symptoms:**
- App tries to connect to Redis and fails
- Logs show "Connection refused" for Redis

**Fix:**
We don't use Redis - the app uses in-memory caching. If you see Redis errors:

1. Check `api/cache_manager.py` doesn't try to connect to Redis
2. Ensure `cache_manager` falls back to in-memory storage

---

## Deployment Checklist

Before deploying to Railway:

- [ ] Run `python verify_api_keys.py` locally - all required APIs pass
- [ ] Commit all changes to GitHub
- [ ] Push to main branch: `git push origin main`
- [ ] Set Railway environment variables from `RAILWAY_ENV_VARS.txt`
- [ ] Add `RAILWAY_ENVIRONMENT=production` variable
- [ ] Deploy from GitHub in Railway
- [ ] Check deployment logs for errors
- [ ] Test `/health` endpoint: `curl https://YOUR-URL.up.railway.app/health`
- [ ] Test `/api/portfolio`: `curl https://YOUR-URL.up.railway.app/api/portfolio`

---

## Step-by-Step Debug Process

### Step 1: Deploy Minimal Version

1. Create a new file in Railway's code editor or push to GitHub:
   ```
   # Procfile
   web: python start_api_minimal.py
   ```

2. Deploy and check logs

3. If minimal version works, the issue is in the main application

4. Revert to full version:
   ```
   # Procfile
   web: python start_api.py
   ```

### Step 2: Check Enhanced Logging

The updated `start_api.py` now includes:
- Python version logging
- Environment variable logging
- Import stage logging
- Detailed error tracebacks

Check Railway logs for these messages to identify where it fails.

### Step 3: Test Locally First

Before deploying to Railway:

```bash
# Set Railway environment variable locally
set RAILWAY_ENVIRONMENT=production  # Windows
export RAILWAY_ENVIRONMENT=production  # Linux/Mac

# Test that data files go to /tmp (won't work on Windows, but validates the logic)
python -c "from utils.data_paths import get_data_path; print(get_data_path('test.json'))"

# Should output: /tmp/test.json
```

### Step 4: Verify Dependencies

```bash
# Locally, ensure all imports work:
python -c "
from fastapi import FastAPI
from anthropic import Anthropic
import alpaca_trade_api
import yfinance
from api.main import app
print('All imports successful')
"
```

If this fails locally, Railway will also fail.

---

## Railway-Specific Fixes Applied

### 1. Data File Paths
- **Before:** `"opportunities_latest.json"` (fails on Railway - read-only filesystem)
- **After:** `get_data_path("opportunities_latest.json")` → `/tmp/opportunities_latest.json`

### 2. Startup Logging
- **Before:** Minimal logging, hard to debug failures
- **After:** Detailed logging at each startup stage

### 3. Error Handling
- **Before:** Generic error messages
- **After:** Full traceback with error type, message, and context

### 4. Port Configuration
- **Before:** Hardcoded port 8000
- **After:** `int(os.getenv("PORT", 8000))` - respects Railway's PORT variable

---

## Useful Railway Commands

**View recent logs:**
```bash
railway logs
```

**Check environment variables:**
```bash
railway variables
```

**Redeploy current version:**
```bash
railway up
```

**Open app in browser:**
```bash
railway open
```

---

## Support Resources

**Railway Docs:**
- Deployments: https://docs.railway.app/guides/deployments
- Environment Variables: https://docs.railway.app/guides/variables
- Logs: https://docs.railway.app/reference/logs

**Project Docs:**
- Main deployment guide: `DEPLOY_NOW.md`
- Production readiness: `PRODUCTION_READY.md`
- API verification: `python verify_api_keys.py`

---

## Quick Test Endpoints

Once deployed, test these endpoints in order:

```bash
# 1. Health check (should always work)
curl https://YOUR-URL.up.railway.app/health

# 2. Portfolio (tests Alpaca connection)
curl https://YOUR-URL.up.railway.app/api/portfolio

# 3. API usage stats (tests file writes)
curl https://YOUR-URL.up.railway.app/api/usage

# 4. Simple analysis (tests Claude API)
curl "https://YOUR-URL.up.railway.app/api/recommendations/analyze/AAPL"
```

If any endpoint fails, check the Railway logs for the specific error.

---

## Emergency Rollback

If deployment breaks production:

1. Go to Railway → Deployments
2. Find last working deployment
3. Click "..." → "Redeploy"

This instantly reverts to the previous version.

---

## Contact

For Railway-specific issues:
- Railway Discord: https://discord.gg/railway
- Railway Support: support@railway.app

For application-specific issues:
- Check logs first
- Review this troubleshooting guide
- Test locally with `RAILWAY_ENVIRONMENT=production` set
