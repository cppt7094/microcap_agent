"""
Morning Brief Generator for Microcap Portfolio
Generates comprehensive pre-market analysis with overnight developments
"""

import sys
import codecs
import logging
from datetime import datetime
from typing import Dict, List, Optional
import alpaca_trade_api as tradeapi
import anthropic
from config import Config
import monitoring_agent as agent
from api_clients import MarketDataManager

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def fetch_market_indices() -> Dict:
    """Fetch current prices for major market indices"""
    try:
        api = tradeapi.REST(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )

        # Fetch index ETFs as proxies
        symbols = ['SPY', 'QQQ', 'IWM']
        quotes = {}

        for symbol in symbols:
            try:
                snapshot = api.get_latest_trade(symbol)
                quotes[symbol] = {
                    'price': float(snapshot.price),
                    'symbol': symbol
                }
            except Exception as e:
                logging.warning(f"Failed to fetch {symbol}: {e}")
                quotes[symbol] = {'price': None, 'symbol': symbol}

        return quotes

    except Exception as e:
        logging.error(f"Error fetching market indices: {e}")
        return {}


def fetch_premarket_movers(portfolio_positions: List[str]) -> Dict:
    """Fetch pre-market data for portfolio positions"""
    try:
        api = tradeapi.REST(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )

        movers = {}
        for symbol in portfolio_positions:
            try:
                # Get latest quote
                quote = api.get_latest_quote(symbol)

                # Get previous close
                bars = api.get_bars(symbol, '1Day', limit=2).df
                if not bars.empty:
                    prev_close = float(bars['close'].iloc[-1])
                    current = float(quote.ask_price)
                    pct_change = ((current - prev_close) / prev_close) * 100

                    if abs(pct_change) >= 3:  # Flag moves >3%
                        movers[symbol] = {
                            'prev_close': prev_close,
                            'current': current,
                            'pct_change': pct_change
                        }
            except Exception as e:
                logging.warning(f"Failed to fetch pre-market data for {symbol}: {e}")

        return movers

    except Exception as e:
        logging.error(f"Error fetching pre-market movers: {e}")
        return {}


def generate_morning_brief_with_claude(portfolio: Dict, analysis_data: List[Dict],
                                      indices: Dict, movers: Dict,
                                      market_data_mgr: Optional[MarketDataManager] = None) -> str:
    """Generate morning brief using Claude AI"""
    try:
        # Build portfolio snapshot
        portfolio_snapshot = "CURRENT PORTFOLIO:\n"
        total_value = portfolio['portfolio_value']

        for pos in portfolio['positions']:
            symbol = pos['symbol']
            value = pos['market_value']
            pct_of_portfolio = (value / total_value) * 100

            portfolio_snapshot += f"- {symbol}: ${value:.2f} ({pct_of_portfolio:.1f}% of portfolio)\n"

        # Build market data section
        market_data = "MARKET DATA:\n"
        if indices:
            market_data += "Futures/Indices:\n"
            for symbol, data in indices.items():
                if data['price']:
                    market_data += f"- {symbol}: ${data['price']:.2f}\n"

        # Build pre-market movers section
        movers_section = "WATCHLIST MOVERS (Pre-market):\n"
        if movers:
            for symbol, data in movers.items():
                movers_section += f"- {symbol}: {data['pct_change']:+.1f}% (${data['current']:.2f})\n"
        else:
            movers_section += "No significant pre-market moves detected\n"

        # Build position analysis
        alerts_section = "PORTFOLIO ALERTS:\n"
        critical_alerts = [a for a in analysis_data if a['action_required']]

        if critical_alerts:
            for alert in critical_alerts:
                alerts_section += f"- {alert['symbol']}: {alert['alert_message']}\n"
        else:
            alerts_section += "No critical alerts\n"

        # Add news and sentiment data if available
        news_section = ""
        sec_section = ""

        if market_data_mgr:
            # Get portfolio symbols
            portfolio_symbols = [pos['symbol'] for pos in portfolio['positions']]

            # Fetch news digest
            news_digest = market_data_mgr.get_portfolio_news_digest(portfolio_symbols)
            if news_digest:
                news_section = "\nOVERNIGHT NEWS:\n"
                for symbol, articles in news_digest.items():
                    if articles:
                        news_section += f"\n{symbol}:\n"
                        for article in articles[:2]:  # Top 2 per stock
                            title = article.get('title') or article.get('headline', 'No title')
                            news_section += f"  • {title}\n"

            # Check for SEC filings
            sec_alerts = market_data_mgr.check_for_sec_alerts(portfolio_symbols)
            if sec_alerts:
                sec_section = "\nRECENT SEC FILINGS:\n"
                for symbol, filings in sec_alerts.items():
                    sec_section += f"{symbol}: {len(filings)} filing(s) - "
                    filing_types = [f['type'] for f in filings[:3]]
                    sec_section += ", ".join(filing_types) + "\n"

        # Create prompt for Claude
        prompt = f"""Generate a concise morning brief for this microcap portfolio using the Project Oriana risk framework.

DATE: {datetime.now().strftime('%A, %B %d, %Y')}

{portfolio_snapshot}

{market_data}

{movers_section}

{alerts_section}

{news_section}

{sec_section}

ANALYSIS REQUIRED:

1. EXECUTIVE SUMMARY (3 bullets max):
   • Most critical development requiring action
   • Market regime assessment (RISK_ON/RISK_OFF)
   • Primary action item for today

2. PORTFOLIO ALERTS:
   • Positions with significant moves
   • Stop loss triggers if any
   • Profit-taking opportunities

3. MARKET REGIME:
   • Current environment assessment
   • Sector signals (AI infrastructure focus)
   • Volatility outlook for microcaps

4. TODAY'S ACTION PLAN:
   HIGH PRIORITY (before 11 AM):
   • Specific executable actions

   MONITOR (throughout day):
   • Watch items and levels

5. RISK ALERTS:
   • Portfolio concentration warnings
   • Technical level alerts
   • Known catalysts (earnings, etc.)

Format: Concise, action-oriented, maximum 250 words total. Use clear headings and bullet points."""

        # Call Claude
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        brief = message.content[0].text
        usage = {
            'input_tokens': message.usage.input_tokens,
            'output_tokens': message.usage.output_tokens
        }

        return brief, usage

    except Exception as e:
        logging.error(f"Error generating morning brief with Claude: {e}", exc_info=True)
        return None, None


def print_morning_brief(portfolio: Dict, analysis_data: List[Dict], brief: str, usage: Dict):
    """Print formatted morning brief"""

    print(f"\n{agent.Colors.BOLD}{agent.Colors.CYAN}{'='*80}")
    print(f"  PROJECT ORIANA - MORNING BRIEF")
    print(f"  {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"{'='*80}{agent.Colors.RESET}\n")

    # Portfolio summary
    print(f"{agent.Colors.BOLD}📊 PORTFOLIO SNAPSHOT{agent.Colors.RESET}")
    print("─" * 80)
    print(f"Total Value: {agent.Colors.BOLD}${portfolio['portfolio_value']:,.2f}{agent.Colors.RESET}")
    print(f"Cash Available: ${portfolio['cash']:,.2f}")
    print(f"Positions: {len(portfolio['positions'])}")
    print()

    # Claude's morning brief
    print(f"{agent.Colors.BOLD}☀️ MORNING BRIEF{agent.Colors.RESET}")
    print("─" * 80)
    print(brief)
    print()

    # API usage
    if usage:
        cost = (usage['input_tokens'] * 0.003 + usage['output_tokens'] * 0.015) / 1000
        print(f"{agent.Colors.BOLD}📊 API Usage{agent.Colors.RESET}")
        print(f"Tokens: {usage['input_tokens']} in / {usage['output_tokens']} out")
        print(f"Cost: ${cost:.4f}")
        print()

    print(f"{agent.Colors.CYAN}{'='*80}{agent.Colors.RESET}\n")


def run_morning_brief(dry_run: bool = False, send_email: bool = False) -> bool:
    """Generate and display morning brief"""
    try:
        # Setup logging
        agent.setup_logging(debug=False)

        print("Generating morning brief...")
        print()

        # Initialize market data manager
        market_data_mgr = None
        if Config.has_market_data_apis():
            print("Initializing market data APIs...")
            market_data_mgr = MarketDataManager()

        # Fetch portfolio data
        portfolio = agent.fetch_portfolio_data(dry_run=dry_run)
        if not portfolio:
            print(f"{agent.Colors.RED}Failed to fetch portfolio data{agent.Colors.RESET}")
            return False

        # Analyze positions
        analysis_data = []
        portfolio_symbols = []

        for position in portfolio['positions']:
            symbol = position['symbol']
            portfolio_symbols.append(symbol)

            if symbol in agent.POSITION_TARGETS:
                analysis = agent.analyze_position(position, agent.POSITION_TARGETS[symbol])
                analysis_data.append(analysis)

        # Fetch market data
        print("Fetching market indices...")
        indices = fetch_market_indices()

        print("Checking pre-market movers...")
        movers = fetch_premarket_movers(portfolio_symbols)

        # Fetch news and SEC data if APIs are available
        if market_data_mgr:
            print("Fetching news and SEC filings...")

        # Generate brief with Claude
        print("Generating AI analysis...")
        brief, usage = generate_morning_brief_with_claude(
            portfolio, analysis_data, indices, movers, market_data_mgr
        )

        if not brief:
            print(f"{agent.Colors.RED}Failed to generate morning brief{agent.Colors.RESET}")
            return False

        # Print brief
        print_morning_brief(portfolio, analysis_data, brief, usage)

        # Send email if requested
        if send_email and not dry_run:
            try:
                from email_alerts import EmailAlertSystem

                email_system = EmailAlertSystem()

                # Create email subject and body
                subject = f"☀️ Morning Brief - {datetime.now().strftime('%b %d, %Y')}"

                body_text = f"""Project Oriana - Morning Brief
{datetime.now().strftime('%A, %B %d, %Y')}

Portfolio Value: ${portfolio['portfolio_value']:,.2f}
Cash Available: ${portfolio['cash']:,.2f}

{brief}

---
Generated by Project Oriana Monitoring Agent
"""

                body_html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: #4CAF50; color: white; padding: 15px; }}
        .content {{ padding: 20px; }}
        .metric {{ padding: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>☀️ Project Oriana - Morning Brief</h2>
        <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
    </div>
    <div class="content">
        <div class="metric"><strong>Portfolio Value:</strong> ${portfolio['portfolio_value']:,.2f}</div>
        <div class="metric"><strong>Cash Available:</strong> ${portfolio['cash']:,.2f}</div>
        <hr>
        <pre style="white-space: pre-wrap; font-family: Arial;">{brief}</pre>
    </div>
</body>
</html>
"""

                print(f"{agent.Colors.CYAN}Sending morning brief email...{agent.Colors.RESET}")
                success = email_system.send_alert_email(subject, body_text, body_html)

                if success:
                    print(f"{agent.Colors.GREEN}✓ Morning brief email sent{agent.Colors.RESET}\n")
                else:
                    print(f"{agent.Colors.YELLOW}⚠ Failed to send email{agent.Colors.RESET}\n")

            except Exception as e:
                print(f"{agent.Colors.YELLOW}⚠ Email error: {e}{agent.Colors.RESET}\n")
                logging.error(f"Email error: {e}", exc_info=True)

        return True

    except Exception as e:
        logging.error(f"Error running morning brief: {e}", exc_info=True)
        print(f"{agent.Colors.RED}Error: {e}{agent.Colors.RESET}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate morning brief for microcap portfolio')
    parser.add_argument('--dry-run', action='store_true', help='Use mock data')
    parser.add_argument('--email', action='store_true', help='Send email with brief')

    args = parser.parse_args()

    success = run_morning_brief(dry_run=args.dry_run, send_email=args.email)
    sys.exit(0 if success else 1)
