# Project Tehama - AI-Powered Microcap Trading Agent

An intelligent portfolio monitoring and analysis system that aggregates data from 6+ financial APIs and uses Claude AI to generate actionable trading insights.

## 🎯 Features

### Core Capabilities
- **Multi-Source Market Intelligence** - Aggregates data from Alpha Vantage, Polygon, FMP, Finnhub, NewsAPI, and SEC API
- **AI-Powered Analysis** - Claude AI analyzes each position with comprehensive market data
- **Market Regime Detection** - Identifies market conditions (trend, volatility, breadth)
- **Automated Morning Briefs** - Comprehensive pre-market reports with actionable insights
- **Real-time Monitoring** - Continuous portfolio tracking via Alpaca API
- **News Sentiment Analysis** - Multi-source news aggregation with AI-powered sentiment scoring
- **Insider Activity Tracking** - Monitors SEC Form 4 filings for insider buy/sell signals
- **Unusual Volume Scanner** - Identifies high-probability setups based on volume anomalies

### Smart Features
- **Position Intelligence** - Each position analyzed with fundamentals, technicals, news, and insider data
- **Opportunity Scoring** - Multi-factor ranking system for new trade setups
- **Risk Management** - Automated stop-loss and profit-taking recommendations
- **Email alerts** - Critical portfolio changes sent via Gmail

## 📂 Project Structure

```
microcap_agent/
├── api_clients.py                  # Multi-source data aggregation
├── enhanced_report_generator.py    # AI-powered report generation
├── run_enhanced_report.py          # Main execution script
├── monitoring_agent.py             # Portfolio monitoring with alerts
├── morning_brief.py                # Morning brief generation
├── continuous_monitor.py           # Continuous monitoring service
├── config.example.py               # API key template (SAFE TO COMMIT)
├── config.py                       # Your actual API keys (NEVER COMMIT)
├── test_*.py                       # API connection tests
├── .gitignore                      # Protects sensitive data
├── ENHANCED_REPORT_README.md       # Detailed documentation
└── reports/                        # Generated reports (not committed)
```

## Setup

### 1. Clone the repository

```bash
cd microcap_agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### Getting API Keys

**Alpaca API:**
1. Sign up at [Alpaca](https://alpaca.markets/)
2. Navigate to Paper Trading dashboard
3. Generate API keys from the dashboard
4. Use `https://paper-api.alpaca.markets` for testing

**Anthropic API:**
1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key
3. Copy the key to your `.env` file

## 📖 Usage

### 🚀 Enhanced Report Generator (NEW!)

**Generate AI-Powered Morning Brief**
```bash
python run_enhanced_report.py
```
Creates comprehensive pre-market analysis with Claude AI, saved to `reports/`

**Quick Market Check**
```bash
python run_enhanced_report.py --quick
```
Fast market regime assessment (trend, volatility, breadth)

**Test All Data Sources**
```bash
python run_enhanced_report.py --test
```
Verify all 6+ APIs are working correctly

**Scheduled Execution**
```bash
python run_enhanced_report.py --schedule
```
Runs automatically at 8:30 AM ET every weekday

### 📊 Portfolio Monitoring

**Morning Brief**
```bash
python monitoring_agent.py --morning
```

**Continuous Monitoring** (every 5 min)
```bash
python monitoring_agent.py --monitor
```

**Market Close Summary**
```bash
python monitoring_agent.py --close
```

### 🧪 Testing

**Test Individual APIs**
```bash
python test_alpaca.py      # Trading platform
python test_anthropic.py   # Claude AI
python test_integration.py # Full integration
```

## Dependencies

- **alpaca-trade-api** - Alpaca trading API client
- **anthropic** - Anthropic Claude AI API client
- **python-dotenv** - Environment variable management
- **google-auth** - Google authentication (for Gmail)
- **google-auth-oauthlib** - OAuth support
- **google-auth-httplib2** - HTTP transport for Google APIs
- **google-api-python-client** - Google API client library

## Configuration Options

Edit `.env` to customize behavior:

```env
# Monitoring interval (minutes)
CHECK_INTERVAL_MINUTES=60

# Alert threshold (percentage change)
ALERT_THRESHOLD_PERCENT=5.0

# Google credentials file path
GOOGLE_CREDENTIALS_FILE=google_credentials.json
```

## Security Notes

- Never commit `.env` file to version control
- Keep `google_credentials.json` private
- Use paper trading for testing
- Rotate API keys regularly

## 🔒 Security - IMPORTANT!

### Before Pushing to GitHub:

1. **NEVER commit `config.py`** - Contains your actual API keys
2. **Verify `.gitignore`** - Ensures sensitive files are excluded
3. **Use `config.example.py`** - Template for other users
4. **Check before committing**:
   ```bash
   git status  # Should NOT show config.py, logs/, or reports/
   ```

### Files NEVER to Commit:
- `config.py` - Your API keys (**CRITICAL**)
- `logs/` - May contain sensitive portfolio data
- `reports/` - Contains your portfolio information
- `credentials.json` - Google OAuth tokens
- `token.json` - Access tokens

## 🛠️ Roadmap

- [x] Basic Alpaca integration
- [x] Basic Claude integration
- [x] Multi-source data aggregation (6+ APIs)
- [x] AI-powered morning briefs
- [x] Market regime detection
- [x] News sentiment analysis
- [x] Insider activity tracking
- [x] Continuous monitoring loop
- [x] Alert detection system
- [x] Gmail notifications
- [ ] Options flow analysis
- [ ] Real-time WebSocket feeds
- [ ] Backtesting framework
- [ ] PDF reports with charts
- [ ] Dashboard interface

## Troubleshooting

### Configuration Errors

If you see "Configuration errors", ensure all required environment variables are set in `.env`:
- ALPACA_API_KEY
- ALPACA_SECRET_KEY
- ANTHROPIC_API_KEY

### API Connection Issues

**Alpaca:**
- Verify API keys are correct
- Check if using correct base URL (paper vs live)
- Ensure account is active

**Anthropic:**
- Verify API key is valid
- Check account has available credits

## License

This project is for educational and personal use.

## Support

For issues or questions, please refer to:
- [Alpaca API Documentation](https://docs.alpaca.markets/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
