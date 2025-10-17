"""
Test integration between Alpaca API and Anthropic Claude
Combines portfolio reading from Alpaca with Claude's analysis using Project Oriana risk rules
"""

import alpaca_trade_api as tradeapi
import anthropic
from config import Config
from datetime import datetime


def get_portfolio_summary():
    """Get a structured summary of the portfolio from Alpaca"""
    try:
        api = tradeapi.REST(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )

        account = api.get_account()
        positions = api.list_positions()

        summary = {
            'account_status': account.status,
            'portfolio_value': float(account.portfolio_value),
            'cash': float(account.cash),
            'equity': float(account.equity),
            'last_equity': float(account.last_equity),
            'positions': []
        }

        for position in positions:
            summary['positions'].append({
                'symbol': position.symbol,
                'qty': float(position.qty),
                'side': position.side,
                'market_value': float(position.market_value),
                'cost_basis': float(position.cost_basis),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc),
                'current_price': float(position.current_price),
                'avg_entry_price': float(position.avg_entry_price)
            })

        return summary

    except Exception as e:
        print(f"Error getting portfolio summary: {e}")
        return None


def format_portfolio_for_analysis(portfolio_data):
    """Format portfolio data into a detailed string for Claude analysis"""

    # Calculate overall metrics
    total_value = portfolio_data['portfolio_value']
    cash = portfolio_data['cash']
    equity = portfolio_data['equity']
    last_equity = portfolio_data['last_equity']
    daily_change = equity - last_equity
    daily_change_pct = (daily_change / last_equity * 100) if last_equity > 0 else 0

    # Build formatted string
    output = f"""
PORTFOLIO OVERVIEW:
==================
Total Portfolio Value: ${total_value:,.2f}
Cash Available: ${cash:,.2f}
Equity Value: ${equity:,.2f}
Daily Change: ${daily_change:,.2f} ({daily_change_pct:+.2f}%)

CURRENT POSITIONS ({len(portfolio_data['positions'])}):
==================
"""

    for idx, pos in enumerate(portfolio_data['positions'], 1):
        pl_pct = pos['unrealized_plpc'] * 100
        pl_sign = "+" if pos['unrealized_pl'] >= 0 else ""

        output += f"""
[{idx}] {pos['symbol']} ({pos['side'].upper()})
    Quantity: {pos['qty']:.0f} shares
    Entry Price: ${pos['avg_entry_price']:.2f}
    Current Price: ${pos['current_price']:.2f}
    Cost Basis: ${pos['cost_basis']:.2f}
    Market Value: ${pos['market_value']:.2f}
    Unrealized P/L: {pl_sign}${pos['unrealized_pl']:.2f} ({pl_sign}{pl_pct:.2f}%)
"""

    return output


def analyze_with_project_oriana_rules(portfolio_data):
    """Analyze portfolio using Claude with Project Oriana risk management rules"""

    try:
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # Format portfolio data
        portfolio_text = format_portfolio_for_analysis(portfolio_data)

        # Build the analysis prompt with Project Oriana rules
        prompt = f"""You are a portfolio risk management analyst following Project Oriana risk rules.
Analyze this REAL portfolio and provide actionable recommendations.

{portfolio_text}

PROJECT ORIANA RISK MANAGEMENT RULES:
=====================================

GAIN THRESHOLDS:
- ALERT at +25% gain: Monitor closely, consider partial profit-taking
- ALERT at +50% gain: RECOMMEND selling 50% to recover original investment
- ALERT at +100% gain: RECOMMEND selling additional 50% of remaining position

LOSS THRESHOLDS:
- ALERT at -10% loss: Monitor closely, review thesis
- ALERT at -15% loss: Strong warning, prepare exit strategy
- HARD STOP at -20% loss: IMMEDIATE SELL REQUIRED to prevent further losses

ANALYSIS REQUIREMENTS:
=====================

1. IMMEDIATE ACTION REQUIRED:
   - List ALL positions that have crossed alert thresholds
   - For each, specify EXACTLY what action to take (sell X shares, set stop loss, etc.)
   - Prioritize by urgency (losses first, then large gains)

2. POSITION-BY-POSITION ANALYSIS:
   - Current status vs risk thresholds
   - Specific recommendation (HOLD / TAKE PROFIT / SELL)
   - Target prices for profit-taking or stop losses

3. PORTFOLIO HEALTH ASSESSMENT:
   - Overall risk level (Low/Medium/High)
   - Diversification quality
   - Cash position adequacy
   - Any systematic risks

4. SUMMARY OF ACTIONS:
   - Immediate actions needed today
   - Positions to monitor closely
   - Overall portfolio adjustments recommended

Be direct and specific. Use actual dollar amounts and share quantities in recommendations.
If a position requires action, state it clearly and urgently."""

        # Call Claude API
        print("\nSending portfolio to Claude for analysis...")

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = message.content[0].text

        # Get usage statistics
        usage = {
            'input_tokens': message.usage.input_tokens,
            'output_tokens': message.usage.output_tokens,
            'total_tokens': message.usage.input_tokens + message.usage.output_tokens
        }

        return response_text, usage

    except Exception as e:
        print(f"Error analyzing portfolio with Claude: {e}")
        return None, None


def print_section_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def test_integration():
    """Test full integration: Fetch portfolio from Alpaca and analyze with Claude"""

    print_section_header("ALPACA + CLAUDE INTEGRATION TEST")
    print("Project Oriana Risk Management Analysis")

    try:
        # Step 1: Validate configuration
        print("\n[Step 1] Validating configuration...")
        Config.validate()
        print("Configuration validated successfully!")

        # Step 2: Fetch portfolio from Alpaca
        print("\n[Step 2] Fetching REAL portfolio data from Alpaca...")
        portfolio_data = get_portfolio_summary()

        if not portfolio_data:
            print("Failed to retrieve portfolio data")
            return False

        print(f"Portfolio retrieved: ${portfolio_data['portfolio_value']:,.2f} total value")
        print(f"Cash available: ${portfolio_data['cash']:,.2f}")
        print(f"Positions found: {len(portfolio_data['positions'])}")

        # Show positions summary
        print("\nPositions:")
        for pos in portfolio_data['positions']:
            pl_pct = pos['unrealized_plpc'] * 100
            pl_sign = "+" if pos['unrealized_pl'] >= 0 else ""
            print(f"  {pos['symbol']}: {pl_sign}{pl_pct:.2f}% P/L")

        # Step 3: Analyze portfolio with Claude using Project Oriana rules
        print("\n[Step 3] Analyzing portfolio with Claude (Project Oriana rules)...")
        analysis, usage = analyze_with_project_oriana_rules(portfolio_data)

        if not analysis:
            print("Failed to get Claude analysis")
            return False

        # Step 4: Display results
        print_section_header("CLAUDE'S RISK ANALYSIS")
        print(analysis)

        # Step 5: Display usage and cost
        print_section_header("API USAGE & COST ESTIMATE")
        print(f"\nInput Tokens: {usage['input_tokens']:,}")
        print(f"Output Tokens: {usage['output_tokens']:,}")
        print(f"Total Tokens: {usage['total_tokens']:,}")

        # Cost calculation for Claude 3.5 Sonnet
        # Pricing: $3 per million input tokens, $15 per million output tokens
        input_cost = (usage['input_tokens'] / 1_000_000) * 3.00
        output_cost = (usage['output_tokens'] / 1_000_000) * 15.00
        total_cost = input_cost + output_cost

        print(f"\nEstimated Cost:")
        print(f"  Input: ${input_cost:.4f}")
        print(f"  Output: ${output_cost:.4f}")
        print(f"  Total: ${total_cost:.4f}")

        print_section_header("TEST SUMMARY")
        print("\n[OK] Configuration validated")
        print("[OK] Portfolio data retrieved from Alpaca")
        print("[OK] Analysis completed by Claude")
        print("[OK] Project Oriana risk rules applied")
        print("\nIntegration test successful!")

        return True

    except Exception as e:
        print(f"\nError during integration test: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    # Run integration test with Project Oriana risk rules
    test_integration()
