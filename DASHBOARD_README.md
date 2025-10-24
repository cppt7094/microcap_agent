# Project Tehama Dashboard - Complete Setup Guide

## 🎉 Dashboard Successfully Deployed!

Your complete Project Tehama trading intelligence dashboard is now live and running.

## 🌐 Access the Dashboard

**Open your browser and navigate to:**
```
http://localhost:8000
```

The dashboard will automatically:
- Load your portfolio data
- Display AI recommendations
- Show agent status
- Display real-time alerts
- Auto-refresh every 30 seconds

## 📊 Dashboard Features

### 1. **Portfolio Tab**
- Real-time portfolio value and performance
- Cash balance
- Daily P/L (dollar and percentage)
- Complete positions table with:
  - Ticker, quantity, entry price
  - Current price and market value
  - Unrealized P/L and daily changes

### 2. **Recommendations Tab**
- AI-generated trading recommendations
- Action types: BUY, SELL, HOLD, ADD, TRIM
- Confidence scores (0-100%)
- Target prices and quantities
- Detailed reasoning from AI agents
- Contributing agent attribution

### 3. **Agents Tab**
- Status of all 5 AI agents:
  - Momentum Agent
  - Sentiment Agent
  - Regime Agent
  - Contrarian Agent
  - Catalyst Agent
- System health monitoring
- Last run times
- Performance metrics per agent

### 4. **Alerts Tab**
- Real-time trading alerts
- Three severity levels:
  - Info (blue) - General notifications
  - Warning (yellow) - Important signals
  - Critical (red) - Urgent alerts
- Alert types:
  - Price alerts
  - News alerts
  - Technical alerts

## 🔧 Technical Stack

### Frontend
- **React 18** - UI framework (from CDN)
- **Tailwind CSS** - Styling (from CDN)
- **Lucide Icons** - Icon library (from CDN)
- **Standalone HTML** - No build process required

### Backend
- **FastAPI** - API framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Python 3.11+**

## 🚀 Quick Start Commands

### Start the Server
```bash
python start_api.py
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Portfolio data
curl http://localhost:8000/api/portfolio

# AI recommendations
curl http://localhost:8000/api/recommendations

# Agent status
curl http://localhost:8000/api/agents/status

# Alerts
curl http://localhost:8000/api/alerts
```

### Run Automated Tests
```bash
python test_api_endpoints.py
```

## 📁 Project Structure

```
microcap_agent/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + routes
│   ├── models.py            # Pydantic models
│   └── services.py          # Business logic
├── frontend/
│   └── index.html           # Complete dashboard (standalone)
├── start_api.py             # Server startup script
└── test_api_endpoints.py   # API testing script
```

## 🎨 Design Features

- **Dark Theme** - Professional slate/blue gradient background
- **Responsive Design** - Works on mobile, tablet, and desktop
- **Real-time Updates** - Auto-refreshes every 30 seconds
- **Loading States** - Smooth loading animations
- **Error Handling** - Graceful error display
- **Accessibility** - Semantic HTML and ARIA labels

## 🔄 Auto-Refresh

The dashboard automatically fetches fresh data every 30 seconds:
- Portfolio positions and values
- New AI recommendations
- Agent status updates
- Latest alerts

## 🌐 CORS Configuration

Currently configured for local development:
- `http://localhost:8000`
- `http://127.0.0.1:8000`
- `http://localhost:3000`
- `file://` protocol (for opening HTML directly)

**Production Note:** Update CORS settings in `api/main.py` before deploying.

## 📊 API Endpoints

### Public Endpoints
- `GET /` - Dashboard homepage
- `GET /health` - Health check

### Data Endpoints
- `GET /api/portfolio` - Portfolio summary with all positions
- `GET /api/recommendations?status={pending|accepted|rejected|executed}` - AI recommendations
- `GET /api/agents/status` - All agent status
- `GET /api/alerts?limit={1-100}` - Recent alerts

### Static Files
- `/static/*` - Frontend assets (mounted from `frontend/` directory)

## 🔍 Troubleshooting

### Dashboard Not Loading?
1. Ensure server is running: `python start_api.py`
2. Check browser console for errors (F12)
3. Verify API endpoints respond: `curl http://localhost:8000/health`

### CORS Errors?
- Open browser DevTools (F12) and check console
- Ensure you're accessing via `http://localhost:8000` (not `file://`)

### Data Not Showing?
1. Check API endpoints manually with curl
2. Verify Alpaca credentials in `config.py`
3. Check server logs for errors

### Port Already in Use?
```bash
# Find process on port 8000
netstat -ano | findstr :8000

# Kill the process (Windows)
taskkill /PID <process_id> /F
```

## 🎯 Next Steps

### Connect Real Broker Data
Update `api/services.py` to use live Alpaca data:
1. Ensure `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` are set in `config.py`
2. Restart the server
3. Portfolio will show real positions

### Customize Recommendations
Modify the AI logic in `enhanced_report_generator.py` to:
- Adjust confidence thresholds
- Add custom trading strategies
- Integrate additional data sources

### Deploy to Production
1. Update CORS settings for your domain
2. Use environment variables for API keys
3. Add authentication/authorization
4. Deploy with gunicorn/nginx
5. Enable HTTPS

## 📖 Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These allow you to:
- Test endpoints directly in browser
- View request/response schemas
- Explore API capabilities

## 🎨 Customization

### Change Theme Colors
Edit `frontend/index.html` - search for color classes:
- `bg-slate-800` → Background color
- `text-blue-400` → Accent color
- Tailwind color palette: https://tailwindcss.com/docs/customizing-colors

### Adjust Refresh Interval
In `frontend/index.html`, change:
```javascript
const REFRESH_INTERVAL = 30000; // milliseconds
```

### Add New Tabs
1. Create new component in `index.html`
2. Add tab to `tabs` array
3. Add conditional render in tab content section

## 🔐 Security Notes

- **Never commit** `config.py` or `.env` files
- API keys are in `.gitignore`
- CORS is currently permissive (development only)
- No authentication enabled (add for production)

## 📞 Support

For issues or questions:
1. Check server logs in terminal
2. Review browser console (F12)
3. Test API endpoints with curl
4. Verify configuration files

---

**🎉 Congratulations!** Your Project Tehama dashboard is fully operational.

**Pro Tip:** Keep the terminal open to monitor server logs and API requests in real-time.
