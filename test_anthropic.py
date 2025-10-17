"""
Test Anthropic API connection and portfolio analysis
Tests Claude API connectivity and basic analysis capabilities
"""

import anthropic
from config import Config


def test_anthropic_connection():
    """Test connection to Anthropic API"""
    print("Testing Anthropic API Connection...")
    print("=" * 50)

    try:
        # Validate configuration
        Config.validate()

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # Test with a simple message
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": "Hello! Please respond with 'API connection successful' if you receive this message."
                }
            ]
        )

        response_text = message.content[0].text
        print(f"\nClaude Response: {response_text}")
        print(f"Model Used: {message.model}")
        print(f"Tokens Used: {message.usage.input_tokens} input, {message.usage.output_tokens} output")

        print("\n" + "=" * 50)
        print("Anthropic API connection test successful!")
        return True

    except Exception as e:
        print(f"\nError testing Anthropic API: {e}")
        return False


def test_portfolio_analysis():
    """Test Claude's ability to analyze portfolio data"""
    print("\nTesting Portfolio Analysis Capabilities...")
    print("=" * 50)

    try:
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # Sample portfolio data
        sample_portfolio = """
        Portfolio Summary:
        - Total Value: $100,000
        - Cash: $20,000
        - Equity: $80,000

        Positions:
        1. AAPL: 50 shares @ $180.00, Current: $175.00, P/L: -$250 (-2.78%)
        2. GOOGL: 30 shares @ $140.00, Current: $145.00, P/L: +$150 (+3.57%)
        3. MSFT: 40 shares @ $380.00, Current: $390.00, P/L: +$400 (+2.63%)
        """

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze this portfolio and provide a brief summary:

{sample_portfolio}

Please provide:
1. Overall portfolio health assessment
2. Key observations about the positions
3. Any notable risks or opportunities"""
                }
            ]
        )

        response_text = message.content[0].text
        print(f"\nClaude's Analysis:\n{response_text}")
        print(f"\nTokens Used: {message.usage.input_tokens} input, {message.usage.output_tokens} output")

        print("\n" + "=" * 50)
        print("Portfolio analysis test successful!")
        return True

    except Exception as e:
        print(f"\nError testing portfolio analysis: {e}")
        return False


def analyze_portfolio_with_claude(portfolio_data):
    """
    Analyze portfolio data using Claude

    Args:
        portfolio_data: Dictionary containing portfolio information

    Returns:
        Analysis string from Claude
    """
    try:
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # Format portfolio data for Claude
        portfolio_summary = f"""
Portfolio Summary:
- Account Status: {portfolio_data.get('account_status', 'N/A')}
- Total Portfolio Value: ${portfolio_data.get('portfolio_value', 0):,.2f}
- Cash: ${portfolio_data.get('cash', 0):,.2f}
- Equity: ${portfolio_data.get('equity', 0):,.2f}

Positions:
"""

        for idx, position in enumerate(portfolio_data.get('positions', []), 1):
            pl_pct = position['unrealized_plpc'] * 100
            portfolio_summary += f"""
{idx}. {position['symbol']}:
   - Quantity: {position['qty']} shares
   - Current Price: ${position['current_price']:,.2f}
   - Avg Entry: ${position['avg_entry_price']:,.2f}
   - Market Value: ${position['market_value']:,.2f}
   - Unrealized P/L: ${position['unrealized_pl']:,.2f} ({pl_pct:.2f}%)
"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"""As a portfolio monitoring agent, analyze this portfolio data:

{portfolio_summary}

Please provide:
1. Overall portfolio health assessment
2. Analysis of each position's performance
3. Risk assessment and diversification analysis
4. Any alerts or concerns that require attention
5. Recommendations for portfolio management

Be concise but thorough in your analysis."""
                }
            ]
        )

        return message.content[0].text

    except Exception as e:
        return f"Error analyzing portfolio: {e}"


if __name__ == "__main__":
    # Run connection test
    test_anthropic_connection()

    # Run portfolio analysis test
    print("\n")
    test_portfolio_analysis()
