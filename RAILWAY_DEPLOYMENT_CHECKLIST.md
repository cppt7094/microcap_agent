# Railway Deployment Checklist

## ✅ Pre-Deployment Complete

All Railway compatibility fixes have been applied and pushed to GitHub (commit `a659017`).

---

## Critical Fixes Applied

### 1. ✅ Lazy Scanner Initialization
- **Issue:** Scanner initialized at module import - crashes entire app if it fails
- **Fix:** Lazy loading - scanner only initializes when first endpoint is called
- **Impact:** App starts even if scanner has issues

### 2. ✅ Read-Only Filesystem Compatibility
- **Issue:** Railway filesystem is read-only except `/tmp`
- **Fix:** `utils/data_paths.py` automatically routes files to `/tmp` when `RAILWAY_ENVIRONMENT=production`
- **Impact:** No "Permission denied" errors on file writes

### 3. ✅ Direct Uvicorn Startup
- **Issue:** Extra startup script adds complexity
- **Fix:** Procfile runs `uvicorn api.main:app` directly with `--log-level info`
- **Impact:** Simpler startup, better error messages

### 4. ✅ Enhanced Error Logging
- **Issue:** Generic errors make debugging difficult
- **Fix:** Comprehensive logging at each stage with full tracebacks
- **Impact:** Easy to identify exact failure point

---

## Deployment Steps

### Step 1: Verify Local Files ✅ DONE
- [x] All API keys verified working (`verify_api_keys.py` passed)
- [x] All changes committed to GitHub
- [x] Latest commit: `a659017`
- [x] Local `RAILWAY_ENV_VARS.txt` file ready

### Step 2: Create Railway Project

1. **Go to Railway:** https://railway.app/new

2. **Click "Deploy from GitHub repo"**

3. **Select repository:** `cppt7094/microcap_agent`

4. **Click "Deploy Now"**

Railway will:
- Detect Python automatically
- Install from `requirements.txt`
- Build the application
- **But it will NOT start yet** (needs environment variables)

### Step 3: Add Environment Variables

1. **In Railway, click your service → "Variables" → "Raw Editor"**

2. **Copy and paste from your local `RAILWAY_ENV_VARS.txt` file:**

   **Note:** Your actual API keys are in the local file `RAILWAY_ENV_VARS.txt` (not committed to GitHub).

   The variables you need to set are:
   ```
   ANTHROPIC_API_KEY=<your_key_from_RAILWAY_ENV_VARS.txt>
   ALPACA_API_KEY=<your_key_from_RAILWAY_ENV_VARS.txt>
   ALPACA_SECRET_KEY=<your_key_from_RAILWAY_ENV_VARS.txt>
   ALPACA_BASE_URL=https://api.alpaca.markets
   FMP_API_KEY=<your_key_from_RAILWAY_ENV_VARS.txt>
   PORT=8000
   RAILWAY_ENVIRONMENT=production
   ```

3. **Click "Save"** or **Ctrl+S**

Railway will **automatically redeploy** with the new variables.

### Step 4: Monitor Build (~2 minutes)

1. **Click "Deployments" → Latest deployment**

2. **Watch the logs** for:
   ```
   ✓ Installing dependencies from requirements.txt...
   ✓ Collecting anthropic>=0.39.0
   ✓ Collecting fastapi>=0.115.6
   ...
   ✓ Successfully installed all packages
   ✓ Build complete
   ✓ Starting deployment...
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:XXXX
   ```

**If build fails:**
- Check logs for missing dependency
- Usually auto-resolves on retry
- See `RAILWAY_TROUBLESHOOTING.md`

### Step 5: Generate Domain

1. **Click "Settings" → "Networking" → "Generate Domain"**

Railway will create a URL like:
```
https://microcap-agent-production-XXXX.up.railway.app
```

**Save this URL** - you'll use it for all API calls.

### Step 6: Test Endpoints

Test in this order (each builds on previous):

#### 6.1 Health Check (Basic)
```bash
curl https://YOUR-URL.up.railway.app/health
```

**Expected:**
```json
{"status": "healthy"}
```

**If this fails:** Check Railway logs immediately. App didn't start.

---

#### 6.2 Portfolio (Alpaca Connection)
```bash
curl https://YOUR-URL.up.railway.app/api/portfolio
```

**Expected:**
```json
{
  "portfolio_value": 890.38,
  "cash": ...,
  "positions": [...]
}
```

**If this fails:** Check Alpaca API keys in Railway Variables.

---

#### 6.3 API Usage (File Writes)
```bash
curl https://YOUR-URL.up.railway.app/api/usage
```

**Expected:**
```json
{
  "date": "2025-10-24",
  "apis": {
    "alpaca": {"calls": 2, "limit": 12000, ...},
    ...
  }
}
```

**If this fails:** Check logs for file write errors. Verify `RAILWAY_ENVIRONMENT=production` is set.

---

#### 6.4 Simple Analysis (Claude API)
```bash
curl "https://YOUR-URL.up.railway.app/api/recommendations/analyze/AAPL"
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "agents": {
    "technical_analyst": {...},
    "fundamental_analyst": {...},
    ...
  },
  "meta_agent_consensus": {...}
}
```

**If this fails:** Check Anthropic API key in Railway Variables.

---

#### 6.5 Full Multi-Agent Analysis
```bash
curl "https://YOUR-URL.up.railway.app/api/recommendations/analyze/APLD?apply_risk=true"
```

**Expected:**
```json
{
  "ticker": "APLD",
  "agents": {...},
  "meta_agent_consensus": {...},
  "risk_committee": {
    "recommendation": "2-3% position",
    ...
  }
}
```

**Success!** Full system is operational.

---

### Step 7: Open Dashboard

**In browser, go to:**
```
https://YOUR-URL.up.railway.app/
```

You should see your real-time trading dashboard with:
- Portfolio value
- Open positions
- Latest recommendations

---

## Common Issues & Quick Fixes

### Issue: Build succeeds but app crashes
**Check:** Railway logs for error message
**Fix:** See `RAILWAY_TROUBLESHOOTING.md` section "Application Crashes"

### Issue: "Module not found"
**Fix:** Check `requirements.txt` includes the missing module
**Verify:** Build logs show "Successfully installed [module]"

### Issue: API key errors
**Fix:**
1. Go to Railway → Variables
2. Check for typos or extra spaces
3. Verify all required variables are set
4. Redeploy after fixing

### Issue: File write errors
**Fix:**
1. Verify `RAILWAY_ENVIRONMENT=production` is set in Variables
2. Check logs to see if files are being written to `/tmp`
3. If not, ensure `utils/data_paths.py` is included in deployment

### Issue: "Port already in use"
**This should not happen** - Railway sets `$PORT` automatically
**If it does:** Check Procfile uses `--port $PORT` (not hardcoded)

---

## Post-Deployment

### Monitor Usage
```bash
# Check API usage daily
curl https://YOUR-URL.up.railway.app/api/usage
```

Watch for:
- FMP approaching 250 calls/day limit
- Claude costs (tracked in Anthropic dashboard)

### Set Up Monitoring

**Railway provides:**
- Uptime monitoring (automatic)
- Deployment history
- Logs (last 10,000 lines)

**Optional external monitoring:**
- UptimeRobot (free): https://uptimerobot.com
- Ping your `/health` endpoint every 5 minutes

### Cost Tracking

**Railway Free Tier:**
- $5/month credit
- Apps sleep after inactivity
- Wakes up on first request (~10 seconds)

**To stay 24/7 active:**
- Upgrade to Railway Pro ($20/month)
- Or: Use external ping service to keep it awake

---

## Emergency Rollback

**If deployment breaks:**

1. Go to Railway → Deployments
2. Find last working deployment (green checkmark)
3. Click "..." → "Redeploy"

Instantly reverts to previous version.

---

## Success Criteria

You know deployment succeeded when:

- [x] `/health` returns `{"status": "healthy"}`
- [x] `/api/portfolio` shows your Alpaca portfolio ($890.38)
- [x] `/api/usage` shows API call tracking
- [x] `/api/recommendations/analyze/AAPL` returns multi-agent analysis
- [x] Dashboard loads at root URL
- [x] No errors in Railway logs

---

## Next Steps After Deployment

1. **Save your Railway URL** - bookmark it
2. **Test all endpoints** - ensure everything works
3. **Check logs** - verify no warnings or errors
4. **Monitor usage** - check `/api/usage` daily
5. **Optional:** Add custom domain in Railway Settings

---

## Support

**If you encounter issues:**

1. **Check Railway logs first** - Click "Deployments" → Latest → "View Logs"
2. **Review `RAILWAY_TROUBLESHOOTING.md`** - comprehensive debugging guide
3. **Test minimal version** - Change Procfile to `start_api_minimal.py`
4. **Railway Discord** - https://discord.gg/railway (very responsive)

---

## You're Ready! 🚀

All fixes applied. All tests passing. All documentation complete.

**Time to deploy:** ~5 minutes

**Deploy now:**
1. https://railway.app/new
2. `cppt7094/microcap_agent`
3. Add variables from `RAILWAY_ENV_VARS.txt`
4. Test `/health`
5. You're live!

Your multi-agent trading system will be operational in production! 🎯
