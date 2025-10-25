"""
Pre-Deployment API Key Verification

Tests all API keys before deploying to Railway to ensure they work.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_anthropic():
    """Test Anthropic API key"""
    try:
        from anthropic import Anthropic
        api_key = os.getenv('ANTHROPIC_API_KEY')

        if not api_key:
            return False, "No API key found"

        client = Anthropic(api_key=api_key)

        # Simple test call
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'OK'"}]
        )

        if response.content[0].text:
            return True, f"Working - Response received"
        else:
            return False, "No response"

    except Exception as e:
        return False, str(e)

def verify_alpaca():
    """Test Alpaca API key"""
    try:
        import alpaca_trade_api as tradeapi

        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')
        base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

        if not api_key or not secret_key:
            return False, "Missing API key or secret"

        api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')

        # Test account access
        account = api.get_account()

        return True, f"Working - Portfolio: ${float(account.portfolio_value):.2f}"

    except Exception as e:
        return False, str(e)

def verify_fmp():
    """Test FMP API key"""
    try:
        import requests

        api_key = os.getenv('FMP_API_KEY')

        if not api_key:
            return False, "No API key found"

        # Test quote endpoint
        url = f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={api_key}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return True, f"Working - AAPL: ${data[0]['price']}"
            else:
                return False, "Empty response"
        else:
            return False, f"HTTP {response.status_code}"

    except Exception as e:
        return False, str(e)

def verify_alpha_vantage():
    """Test Alpha Vantage API key"""
    try:
        import requests

        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')

        if not api_key:
            return False, "No API key found"

        # Test quote endpoint
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={api_key}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'Global Quote' in data and data['Global Quote']:
                return True, f"Working - AAPL quote received"
            elif 'Note' in data:
                return False, "Rate limited (normal for free tier)"
            else:
                return False, "Invalid response"
        else:
            return False, f"HTTP {response.status_code}"

    except Exception as e:
        return False, str(e)

def verify_finnhub():
    """Test Finnhub API key"""
    try:
        import requests

        api_key = os.getenv('FINNHUB_API_KEY')

        if not api_key:
            return False, "No API key found"

        # Test quote endpoint
        url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'c' in data and data['c'] > 0:  # 'c' is current price
                return True, f"Working - AAPL: ${data['c']}"
            else:
                return False, "Invalid response"
        else:
            return False, f"HTTP {response.status_code}"

    except Exception as e:
        return False, str(e)

def main():
    """Run all API key verification tests"""

    print("=" * 80)
    print("API KEY VERIFICATION - Pre-Deployment Check")
    print("=" * 80)
    print()

    tests = [
        ("Anthropic (Claude)", verify_anthropic, True),   # Required
        ("Alpaca Trading", verify_alpaca, True),          # Required
        ("FMP (Fundamentals)", verify_fmp, True),         # Required
        ("Alpha Vantage", verify_alpha_vantage, False),   # Optional (has fallback)
        ("Finnhub", verify_finnhub, False),               # Optional
    ]

    results = []
    all_required_pass = True

    for name, test_func, required in tests:
        print(f"Testing {name}...", end=" ")
        success, message = test_func()

        results.append((name, success, message, required))

        if success:
            print(f"[OK] {message}")
        else:
            if required:
                print(f"[FAIL] REQUIRED - {message}")
                all_required_pass = False
            else:
                print(f"[WARN] OPTIONAL - {message}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for name, success, message, required in results:
        status = "[OK]" if success else ("[FAIL]" if required else "[WARN]")
        req_text = " (REQUIRED)" if required else " (optional)"
        print(f"{status} {name}{req_text}")

    print()

    if all_required_pass:
        print("[SUCCESS] ALL REQUIRED API KEYS WORKING")
        print()
        print("Ready to deploy! Your Railway environment variables should be:")
        print()
        print("ANTHROPIC_API_KEY=" + os.getenv('ANTHROPIC_API_KEY', 'NOT_SET'))
        print("ALPACA_API_KEY=" + os.getenv('ALPACA_API_KEY', 'NOT_SET'))
        print("ALPACA_SECRET_KEY=" + os.getenv('ALPACA_SECRET_KEY', 'NOT_SET')[:20] + "...")
        print("ALPACA_BASE_URL=" + os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'))
        print("FMP_API_KEY=" + os.getenv('FMP_API_KEY', 'NOT_SET'))
        print("ALPHA_VANTAGE_API_KEY=" + os.getenv('ALPHA_VANTAGE_API_KEY', 'NOT_SET'))
        print("FINNHUB_API_KEY=" + os.getenv('FINNHUB_API_KEY', 'NOT_SET'))
        print("PORT=8000")
        print()
        print("Copy these to Railway's environment variables section.")
        print()
        return 0
    else:
        print("[ERROR] SOME REQUIRED API KEYS FAILED")
        print()
        print("Fix these issues before deploying:")
        for name, success, message, required in results:
            if required and not success:
                print(f"  - {name}: {message}")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
