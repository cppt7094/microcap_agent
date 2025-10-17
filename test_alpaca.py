"""
Test Alpaca API connection and portfolio reading
Tests connectivity, account info, positions, orders, and market status
"""

import alpaca_trade_api as tradeapi
from config import Config
from datetime import datetime, timezone


def print_section_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_account_info():
    """Test getting account information"""
    print_section_header("ACCOUNT INFORMATION")

    try:
        api = tradeapi.REST(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )

        account = api.get_account()

        # Account Status
        print(f"\nAccount Status: {account.status}")
        print(f"Account Number: {account.account_number}")
        print(f"Trading Blocked: {account.trading_blocked}")
        print(f"Account Blocked: {account.account_blocked}")
        print(f"Pattern Day Trader: {account.pattern_day_trader}")

        # Portfolio Values
        print(f"\nPortfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"Cash: ${float(account.cash):,.2f}")
        print(f"Buying Power: ${float(account.buying_power):,.2f}")
        print(f"Equity: ${float(account.equity):,.2f}")

        # Additional Account Details
        last_equity = float(account.last_equity)
        equity = float(account.equity)
        daily_change = equity - last_equity
        daily_change_pct = (daily_change / last_equity * 100) if last_equity > 0 else 0

        print(f"\nLast Equity: ${last_equity:,.2f}")
        print(f"Daily Change: ${daily_change:,.2f} ({daily_change_pct:+.2f}%)")

        print("\nAccount test successful!")
        return api, True

    except Exception as e:
        print(f"\nError getting account info: {e}")
        print(f"Error type: {type(e).__name__}")
        return None, False


def test_positions(api):
    """Test getting current positions"""
    print_section_header("CURRENT POSITIONS")

    try:
        positions = api.list_positions()

        if not positions:
            print("\nNo open positions found.")
            return True

        print(f"\nTotal Positions: {len(positions)}\n")

        for idx, position in enumerate(positions, 1):
            symbol = position.symbol
            qty = float(position.qty)
            side = position.side
            market_value = float(position.market_value)
            unrealized_pl = float(position.unrealized_pl)
            unrealized_plpc = float(position.unrealized_plpc) * 100
            current_price = float(position.current_price)
            avg_entry_price = float(position.avg_entry_price)
            cost_basis = float(position.cost_basis)

            pl_sign = "+" if unrealized_pl >= 0 else ""

            print(f"[{idx}] {symbol} ({side.upper()})")
            print(f"    Quantity: {qty:,.0f} shares")
            print(f"    Entry Price: ${avg_entry_price:,.2f}")
            print(f"    Current Price: ${current_price:,.2f}")
            print(f"    Market Value: ${market_value:,.2f}")
            print(f"    Cost Basis: ${cost_basis:,.2f}")
            print(f"    Unrealized P/L: {pl_sign}${unrealized_pl:,.2f} ({pl_sign}{unrealized_plpc:.2f}%)")
            print()

        print("Positions test successful!")
        return True

    except Exception as e:
        print(f"\nError getting positions: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def test_recent_orders(api):
    """Test getting recent orders"""
    print_section_header("RECENT ORDERS (Last 5)")

    try:
        orders = api.list_orders(
            status='all',
            limit=5,
            nested=False
        )

        if not orders:
            print("\nNo orders found.")
            return True

        print(f"\nShowing {len(orders)} most recent orders:\n")

        for idx, order in enumerate(orders, 1):
            symbol = order.symbol
            side = order.side
            qty = order.qty
            order_type = order.type
            status = order.status
            filled_qty = order.filled_qty if hasattr(order, 'filled_qty') else '0'

            # Format timestamps
            submitted_at = order.submitted_at
            if isinstance(submitted_at, str):
                try:
                    submitted_at = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                except:
                    pass

            print(f"[{idx}] {symbol} - {side.upper()} {qty} shares")
            print(f"    Order Type: {order_type}")
            print(f"    Status: {status}")
            print(f"    Filled: {filled_qty}/{qty}")

            if hasattr(order, 'limit_price') and order.limit_price:
                print(f"    Limit Price: ${float(order.limit_price):,.2f}")

            if hasattr(order, 'filled_avg_price') and order.filled_avg_price:
                print(f"    Avg Fill Price: ${float(order.filled_avg_price):,.2f}")

            print(f"    Submitted: {submitted_at}")
            print()

        print("Orders test successful!")
        return True

    except Exception as e:
        print(f"\nError getting orders: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def test_market_clock(api):
    """Test getting market clock status"""
    print_section_header("MARKET CLOCK STATUS")

    try:
        clock = api.get_clock()

        print(f"\nCurrent Time (UTC): {clock.timestamp}")
        print(f"Market Status: {'OPEN' if clock.is_open else 'CLOSED'}")
        print(f"\nNext Open: {clock.next_open}")
        print(f"Next Close: {clock.next_close}")

        if clock.is_open:
            print("\nThe market is currently open for trading.")
        else:
            print("\nThe market is currently closed.")

        print("\nMarket clock test successful!")
        return True

    except Exception as e:
        print(f"\nError getting market clock: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def test_alpaca_connection():
    """Run all Alpaca API tests"""
    print("\n" + "=" * 70)
    print(" ALPACA API CONNECTION TEST")
    print("=" * 70)

    try:
        # Validate configuration
        print("\nValidating configuration...")
        Config.validate()
        print("Configuration validated successfully!")

        # Test 1: Account Info
        api, success = test_account_info()
        if not success:
            return False

        # Test 2: Positions
        if not test_positions(api):
            return False

        # Test 3: Recent Orders
        if not test_recent_orders(api):
            return False

        # Test 4: Market Clock
        if not test_market_clock(api):
            return False

        # Summary
        print_section_header("TEST SUMMARY")
        print("\n[OK] All tests passed successfully!")
        print("[OK] Account information retrieved")
        print("[OK] Positions retrieved")
        print("[OK] Recent orders retrieved")
        print("[OK] Market clock status retrieved")
        print("\nAlpaca API is working correctly!")

        return True

    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        return False
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def get_portfolio_summary():
    """Get a structured summary of the portfolio"""
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
            'positions': []
        }

        for position in positions:
            summary['positions'].append({
                'symbol': position.symbol,
                'qty': position.qty,
                'market_value': float(position.market_value),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc),
                'current_price': float(position.current_price),
                'avg_entry_price': float(position.avg_entry_price)
            })

        return summary

    except Exception as e:
        print(f"Error getting portfolio summary: {e}")
        return None


if __name__ == "__main__":
    test_alpaca_connection()
