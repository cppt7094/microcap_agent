"""
Configuration management for the portfolio monitoring agent.
Loads environment variables and provides centralized access to API keys and settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for managing environment variables and settings."""

    # Alpaca API Configuration
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
    ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

    # Anthropic API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

    # Email Configuration (for SMTP notifications)
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')

    # Google API Configuration (for Gmail API notifications - optional)
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')

    # Monitoring Configuration
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '60'))
    ALERT_THRESHOLD_PERCENT = float(os.getenv('ALERT_THRESHOLD_PERCENT', '5.0'))

    # Market Data API Configuration
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
    FINNHUB_KEY = os.getenv('FINNHUB_KEY')
    FMP_API_KEY = os.getenv('FMP_API_KEY')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    SEC_API_KEY = os.getenv('SEC_API_KEY')
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

    @classmethod
    def validate(cls, require_email=False):
        """
        Validate that required configuration values are present.

        Args:
            require_email: If True, email credentials are required. Default False.
        """
        required_vars = {
            'ALPACA_API_KEY': cls.ALPACA_API_KEY,
            'ALPACA_SECRET_KEY': cls.ALPACA_SECRET_KEY,
            'ANTHROPIC_API_KEY': cls.ANTHROPIC_API_KEY,
        }

        # Add email credentials to required vars if needed
        if require_email:
            required_vars['EMAIL_ADDRESS'] = cls.EMAIL_ADDRESS
            required_vars['EMAIL_APP_PASSWORD'] = cls.EMAIL_APP_PASSWORD

        missing = [key for key, value in required_vars.items() if not value]

        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}\n"
            error_msg += "Please check your .env file and ensure these variables are set.\n\n"
            error_msg += "Required variables:\n"
            for var in missing:
                error_msg += f"  - {var}\n"

            raise ValueError(error_msg)

        return True

    @classmethod
    def print_config(cls):
        """Print configuration (masking sensitive values)."""
        def mask_key(key):
            if not key:
                return "NOT SET"
            return f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"

        def mask_email(email):
            if not email:
                return "NOT SET"
            parts = email.split('@')
            if len(parts) == 2:
                username = parts[0][:2] + "***" if len(parts[0]) > 2 else "***"
                return f"{username}@{parts[1]}"
            return "****"

        print("Configuration:")
        print(f"  Alpaca API Key: {mask_key(cls.ALPACA_API_KEY)}")
        print(f"  Alpaca Secret Key: {mask_key(cls.ALPACA_SECRET_KEY)}")
        print(f"  Alpaca Base URL: {cls.ALPACA_BASE_URL}")
        print(f"  Anthropic API Key: {mask_key(cls.ANTHROPIC_API_KEY)}")
        print(f"  Email Address: {mask_email(cls.EMAIL_ADDRESS)}")
        print(f"  Email App Password: {mask_key(cls.EMAIL_APP_PASSWORD)}")
        print(f"  Check Interval: {cls.CHECK_INTERVAL_MINUTES} minutes")
        print(f"  Alert Threshold: {cls.ALERT_THRESHOLD_PERCENT}%")

    @classmethod
    def is_paper_trading(cls):
        """Check if using paper trading account."""
        return 'paper' in cls.ALPACA_BASE_URL.lower() if cls.ALPACA_BASE_URL else False

    @classmethod
    def has_email_config(cls):
        """Check if email configuration is present."""
        return bool(cls.EMAIL_ADDRESS and cls.EMAIL_APP_PASSWORD)

    @classmethod
    def has_market_data_apis(cls):
        """Check if market data API keys are configured."""
        return any([
            cls.ALPHA_VANTAGE_KEY,
            cls.FINNHUB_KEY,
            cls.FMP_API_KEY,
            cls.NEWS_API_KEY,
            cls.SEC_API_KEY,
            cls.POLYGON_API_KEY
        ])


if __name__ == "__main__":
    # Test configuration loading
    try:
        Config.validate()
        Config.print_config()
        print("\nConfiguration loaded successfully!")
    except ValueError as e:
        print(f"Configuration error: {e}")
