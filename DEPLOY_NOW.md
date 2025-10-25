# Deploy to Railway - Step by Step

## ✅ Pre-Deployment Verification PASSED

All required API keys tested and working:
- ✅ Anthropic (Claude) - Working
- ✅ Alpaca Trading - Portfolio: $890.38
- ✅ FMP (Fundamentals) - Working

---

## Step 1: Go to Railway (30 seconds)

**URL:** https://railway.app/new

1. Click **"Deploy from GitHub repo"**
2. Select: `cppt7094/microcap_agent`
3. Click **"Deploy Now"**

Railway will auto-detect Python and start building.

---

## Step 2: Add Environment Variables (1 minute)

### Click "Variables" → "Raw Editor"

**Your API keys have been verified and saved in:**
- `RAILWAY_ENV_VARS.txt` (local file - not in GitHub)

**Copy the contents of that file and paste into Railway's Raw Editor.**

Or manually add these variables:

```
ANTHROPIC_API_KEY=your_key_from_env_file
ALPACA_API_KEY=your_key_from_env_file
ALPACA_SECRET_KEY=your_key_from_env_file
ALPACA_BASE_URL=https://api.alpaca.markets
FMP_API_KEY=your_key_from_env_file
PORT=8000
```

**Click "Save"**

Railway will automatically redeploy with the new variables.

---

## Step 3: Wait for Build (2 minutes)

Click **"Deployments"** → Watch the build log

You should see:
```
✓ Installing dependencies...
✓ Building application...
✓ Starting server...
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## Step 4: Get Your URL (10 seconds)

Railway generates a URL like:
```
https://microcap-agent-production-XXXX.up.railway.app
```

Find it in:
- **Settings** → **Domains** → **Generate Domain**

Or it's shown automatically in the deployment overview.

---

## Step 5: Test Your Deployment (1 minute)

### 5.1 Health Check
```bash
curl https://YOUR-URL.up.railway.app/health
```

Should return:
```json
{"status": "healthy"}
```

### 5.2 Test Portfolio
```bash
curl https://YOUR-URL.up.railway.app/api/portfolio
```

Should return your real Alpaca portfolio ($890.38).

### 5.3 Test Multi-Agent Analysis
```bash
curl "https://YOUR-URL.up.railway.app/api/recommendations/analyze/APLD?apply_risk=true"
```

Should return:
- 4 agent votes
- Meta-Agent consensus
- Risk Committee position sizing
- Final recommendation

### 5.4 Open Dashboard
```bash
# In browser, go to:
https://YOUR-URL.up.railway.app/
```

You should see your real-time trading dashboard.

---

## Step 6: Verify Logs (30 seconds)

Click **"Deployments"** → Latest → **"View Logs"**

Look for:
```
✓ Analyst team initialized (Technical, Fundamental, Sentiment, Risk)
✓ Risk Committee initialized
✓ Meta-Agent initialized
✓ Alpaca REST API initialized successfully
✓ Portfolio: $890.38
```

---

## Common Issues & Fixes

### Issue: "Build failed"
**Fix:** Check logs for missing dependencies. Usually auto-resolved on retry.

### Issue: "API key error"
**Fix:** Verify environment variables in Railway → Variables. Make sure no extra spaces.

### Issue: "Application error"
**Fix:** Check logs. Usually means:
- Missing environment variable
- API key typo
- Need to redeploy after adding variables

### Issue: Slow first request
**Normal:** Railway apps sleep after inactivity. First request wakes it (~10 seconds).

---

## Your System is Ready

Once deployed, you have:

✅ **4-Agent Analysis** - Technical, Fundamental, Sentiment, Risk
✅ **Meta-Agent** - Anti-groupthink detection
✅ **Risk Committee** - Automated position sizing
✅ **Opportunity Scanner** - 40+ ticker screening
✅ **Real-time Dashboard** - Live portfolio tracking
✅ **API Monitoring** - Usage tracking

---

## API Endpoints Available

All endpoints at: `https://YOUR-URL.up.railway.app`

```
GET /                                      - Dashboard
GET /health                                - Health check
GET /api/portfolio                         - Real-time portfolio
GET /api/recommendations                   - Cached recommendations
GET /api/recommendations/analyze/{ticker}  - Live multi-agent analysis
GET /api/opportunities/scan                - Market scan
GET /api/opportunities/latest              - Cached opportunities
GET /api/usage                             - API usage stats
```

---

## Example API Calls

### Analyze APLD with Full Pipeline
```bash
curl "https://YOUR-URL/api/recommendations/analyze/APLD?apply_risk=true"
```

### Scan for Opportunities (min 60 score)
```bash
curl "https://YOUR-URL/api/opportunities/scan?min_score=60"
```

### Check API Usage
```bash
curl "https://YOUR-URL/api/usage"
```

---

## Cost Monitoring

### Railway Free Tier:
- $5/month credit
- Sleeps after inactivity
- Upgrade to Pro ($20/month) for 24/7

### API Usage (per analysis):
- Claude: 4 calls (~$0.012)
- FMP: 8 calls
- Alpaca: 2 calls

### Daily Limits:
- FMP: 250 calls/day → ~30 analyses/day
- Alpaca: 12,000 calls/day
- Claude: Unlimited (pay per use)

**Monitor usage:** `https://YOUR-URL/api/usage`

---

## Next Steps After Deployment

1. **Save your Railway URL** - You'll use this for all API calls
2. **Bookmark the dashboard** - `https://YOUR-URL/`
3. **Set up monitoring** - Check `/api/usage` daily
4. **Test live analysis** - Run a few tickers
5. **Optional: Add custom domain** - Railway Settings → Domains

---

## Security Note

✅ All API keys are in Railway environment variables (encrypted)
✅ Not in code or GitHub
✅ HTTPS enabled by default
✅ CORS configured

**Don't share your Railway URL publicly** unless you add authentication.

---

## Support

**Railway Docs:** https://docs.railway.app
**GitHub Repo:** https://github.com/cppt7094/microcap_agent
**System Docs:** See `PRODUCTION_READY.md`

---

## 🚀 Ready to Deploy!

**Time required:** 5 minutes total

**Steps:**
1. Go to https://railway.app/new
2. Deploy from GitHub: `cppt7094/microcap_agent`
3. Add environment variables (copy from above)
4. Wait for build
5. Test endpoints

**Then start using:** `curl "https://YOUR-URL/api/recommendations/analyze/APLD?apply_risk=true"`

Your multi-agent trading system will be live! 🎯
