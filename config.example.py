"""
Configuration Template for Project Tehama - Microcap Trading Agent
Copy this file to config.py and fill in your actual API keys
"""

class Config:
    """
    API Configuration

    INSTRUCTIONS:
    1. Copy this file to 'config.py'
    2. Replace all placeholder values with your actual API keys
    3. NEVER commit config.py to version control (it's in .gitignore)
    """

    # ========================================================================
    # Trading Platform
    # ========================================================================

    # Alpaca Markets (https://alpaca.markets/)
    ALPACA_API_KEY = 'your_alpaca_api_key_here'
    ALPACA_SECRET_KEY = 'your_alpaca_secret_key_here'
    ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'  # Paper trading
    # ALPACA_BASE_URL = 'https://api.alpaca.markets'  # Live trading (uncomment when ready)

    # ========================================================================
    # Market Data APIs
    # ========================================================================

    # Alpha Vantage (https://www.alphavantage.co/)
    # Free tier: 25 requests/day, 5 requests/minute
    ALPHA_VANTAGE_KEY = 'your_alpha_vantage_key_here'

    # Polygon.io (https://polygon.io/)
    # Free tier: 5 requests/minute
    POLYGON_API_KEY = 'your_polygon_api_key_here'

    # Financial Modeling Prep (https://financialmodelingprep.com/)
    # Free tier: 250 requests/day
    FMP_API_KEY = 'your_fmp_api_key_here'

    # Finnhub (https://finnhub.io/)
    # Free tier: 60 requests/minute
    FINNHUB_KEY = 'your_finnhub_key_here'

    # News API (https://newsapi.org/)
    # Free tier: 100 requests/day
    NEWS_API_KEY = 'your_newsapi_key_here'

    # SEC API (https://sec-api.io/)
    # Free tier: 10 requests/day
    SEC_API_KEY = 'your_sec_api_key_here'

    # ========================================================================
    # AI Services
    # ========================================================================

    # Anthropic Claude (https://console.anthropic.com/)
    ANTHROPIC_API_KEY = 'your_anthropic_api_key_here'

    # ========================================================================
    # Communication
    # ========================================================================

    # Gmail for alerts (optional)
    GMAIL_USER = 'your_email@gmail.com'
    GMAIL_APP_PASSWORD = 'your_gmail_app_password_here'  # Not your regular password!
    ALERT_EMAIL = 'your_alert_recipient@gmail.com'

    # ========================================================================
    # Google Drive (optional - for backups)
    # ========================================================================

    GOOGLE_DRIVE_FOLDER_ID = 'your_google_drive_folder_id_here'

    # ========================================================================
    # Validation
    # ========================================================================

    @classmethod
    def validate(cls):
        """Validate that critical API keys are set"""
        required_keys = {
            'ALPACA_API_KEY': cls.ALPACA_API_KEY,
            'ALPACA_SECRET_KEY': cls.ALPACA_SECRET_KEY,
            'ANTHROPIC_API_KEY': cls.ANTHROPIC_API_KEY,
        }

        missing = []
        for key_name, key_value in required_keys.items():
            if not key_value or 'your_' in key_value.lower() or key_value == '':
                missing.append(key_name)

        if missing:
            raise ValueError(
                f"Missing required API keys in config.py: {', '.join(missing)}\n"
                f"Please copy config.example.py to config.py and add your actual API keys."
            )

        print("✓ Required API keys validated")

        # Warn about optional keys
        optional_keys = {
            'ALPHA_VANTAGE_KEY': cls.ALPHA_VANTAGE_KEY,
            'POLYGON_API_KEY': cls.POLYGON_API_KEY,
            'FMP_API_KEY': cls.FMP_API_KEY,
            'FINNHUB_KEY': cls.FINNHUB_KEY,
            'NEWS_API_KEY': cls.NEWS_API_KEY,
            'SEC_API_KEY': cls.SEC_API_KEY,
        }

        not_configured = []
        for key_name, key_value in optional_keys.items():
            if not key_value or 'your_' in key_value.lower() or key_value == '':
                not_configured.append(key_name)

        if not_configured:
            print(f"⚠ Optional API keys not configured: {', '.join(not_configured)}")
            print(f"   Some features may be limited. Add these keys for full functionality.")


# ============================================================================
# API Rate Limits (for reference)
# ============================================================================

RATE_LIMITS = {
    'alpha_vantage': {
        'free': '25 requests/day, 5 requests/minute',
        'paid': 'Varies by plan'
    },
    'polygon': {
        'free': '5 requests/minute',
        'starter': '100 requests/minute ($29/mo)',
        'developer': '1000 requests/minute ($99/mo)'
    },
    'fmp': {
        'free': '250 requests/day',
        'starter': '300 requests/day ($14/mo)',
        'premium': 'Unlimited ($29/mo)'
    },
    'finnhub': {
        'free': '60 requests/minute',
        'paid': 'Varies by plan'
    },
    'newsapi': {
        'free': '100 requests/day',
        'paid': '250-100,000 requests/day'
    },
    'sec_api': {
        'free': '10 requests/day',
        'paid': 'Varies by plan'
    },
    'anthropic_claude': {
        'pricing': 'Pay per token',
        'sonnet_4': '$3/M input tokens, $15/M output tokens'
    }
}
