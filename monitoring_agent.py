"""
Portfolio Monitoring Agent - Project Oriana Framework
Monitors portfolio positions against defined entry prices and risk thresholds
Generates actionable morning briefs with Claude AI analysis
"""

import sys
import os
import argparse
import time
import logging
import json
import signal
from pathlib import Path
import alpaca_trade_api as tradeapi
import anthropic
from config import Config
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from api_clients import MarketDataManager

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


# ============================================================================
# GLOBAL STATE MANAGEMENT
# ============================================================================

# Monitoring state
class MonitoringState:
    """Tracks alerts sent and monitoring statistics"""
    def __init__(self):
        self.alerts_sent_today: Set[str] = set()
        self.start_time: Optional[datetime] = None
        self.checks_performed: int = 0
        self.alerts_count: int = 0
        self.current_date: Optional[str] = None
        self.shutdown_requested: bool = False

    def reset_for_new_day(self):
        """Reset daily tracking at market open"""
        today = datetime.now().strftime('%Y-%m-%d')
        if self.current_date != today:
            self.alerts_sent_today.clear()
            self.current_date = today
            logging.info(f"Reset alert tracking for new day: {today}")

    def has_sent_alert(self, alert_key: str) -> bool:
        """Check if alert was already sent today"""
        return alert_key in self.alerts_sent_today

    def mark_alert_sent(self, alert_key: str):
        """Mark alert as sent"""
        self.alerts_sent_today.add(alert_key)
        self.alerts_count += 1

    def get_summary(self) -> str:
        """Get monitoring session summary"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            hours = duration.total_seconds() / 3600
            return f"Monitored for {hours:.1f} hours, performed {self.checks_performed} checks, sent {self.alerts_count} alerts"
        return "No monitoring session active"

# Global monitoring state
monitoring_state = MonitoringState()


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging(debug: bool = False):
    """Setup logging with file rotation"""
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Log file with date
    log_file = log_dir / f"monitoring_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Console handler (only for errors and warnings)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    # Configure root logger
    logging.root.setLevel(log_level)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)

    logging.info("="*80)
    logging.info("Monitoring agent started")
    logging.info(f"Log file: {log_file}")
    logging.info("="*80)


# ============================================================================
# PROJECT ORIANA PORTFOLIO CONFIGURATION
# ============================================================================

# Portfolio tracking
INITIAL_INVESTMENT = 753.71  # Total capital deployed

# Known entry prices and target allocations
POSITION_TARGETS = {
    'APLD': {
        'entry_price': 21.58,
        'current_shares': 3,
        'target_shares': 6,
        'target_value': 150.00,
        'status': 'pending_add',  # pending_add, complete, trimmed
        'pending_add': 3,
        'notes': 'Need to add 3 more shares (~$85)'
    },
    'NTLA': {
        'entry_price': 22.01,
        'current_shares': 6,
        'target_shares': 6,
        'target_value': 140.00,
        'status': 'complete',
        'pending_add': 0,
        'notes': 'Recently added 3 shares - AT TARGET'
    },
    'SOUN': {
        'entry_price': 16.08,
        'current_shares': 5,
        'target_shares': 7,
        'target_value': 120.00,
        'status': 'pending_add',
        'pending_add': 2,
        'notes': 'Need to add 2 more shares (~$40)'
    },
    'WYFI': {
        'entry_price': 32.50,
        'current_shares': 2,
        'target_shares': 4,
        'target_value': 120.00,
        'status': 'pending_add',
        'pending_add': 2,
        'notes': 'Need to add 2 more shares (~$55)'
    },
    'TSSI': {
        'entry_price': 17.30,  # Note: Using corrected entry from test results
        'current_shares': 3,
        'target_shares': 3,
        'target_value': 175.00,
        'status': 'complete',
        'pending_add': 0,
        'notes': 'Holding as is - AT TARGET'
    },
    'CRWV': {
        'entry_price': 138.45,
        'current_shares': 0.77,
        'target_shares': 0.77,
        'target_value': 80.00,
        'status': 'trimmed',
        'pending_add': 0,
        'notes': 'Trimmed to target'
    },
    'RGTI': {
        'entry_price': None,  # To be determined when position opens
        'current_shares': 0,
        'target_shares': 50,
        'target_value': 120.00,
        'status': 'pending_new',
        'pending_add': 50,
        'notes': 'New position pending (~$120)'
    }
}

# Risk management thresholds
GAIN_THRESHOLDS = {
    'alert': 0.25,      # +25% - Monitor closely
    'strong': 0.50,     # +50% - Recover investment
    'critical': 1.00,   # +100% - Sell 50%
    'extreme': 2.00     # +200% - Sell 75%
}

LOSS_THRESHOLDS = {
    'alert': -0.10,     # -10% - Review thesis
    'strong': -0.15,    # -15% - Approaching stop
    'hard_stop': -0.20  # -20% - IMMEDIATE EXIT
}

THRESHOLD_PROXIMITY = 0.05  # Within 5% of threshold


# ============================================================================
# ANSI COLOR CODES FOR TERMINAL OUTPUT
# ============================================================================

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Status colors
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'


# Signal handler for graceful shutdown (defined after Colors class)
def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    monitoring_state.shutdown_requested = True
    print(f"\n\n{Colors.YELLOW}Shutdown requested... finishing current operation{Colors.RESET}")

signal.signal(signal.SIGINT, signal_handler)


# ============================================================================
# MARKET HOURS CHECKING
# ============================================================================

def check_market_status(dry_run=False):
    """
    Check if market is currently open using Alpaca clock

    Returns:
        Tuple of (is_open: bool, next_open: datetime, next_close: datetime, clock_obj)
    """
    if dry_run:
        # Mock market as open for dry-run
        now = datetime.now()
        return (True, now, now + timedelta(hours=2), None)

    try:
        api = tradeapi.REST(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )

        clock = api.get_clock()
        return (clock.is_open, clock.next_open, clock.next_close, clock)

    except Exception as e:
        logging.error(f"Error checking market status: {e}")
        return (False, None, None, None)


# ============================================================================
# BENCHMARK TRACKING
# ============================================================================

# Benchmark ETFs to track
BENCHMARKS = {
    'SPY': 'S&P 500',
    'QQQ': 'Nasdaq 100',
    'IBB': 'Biotech',
    'IWM': 'Russell 2000'
}


def fetch_benchmark_data(dry_run: bool = False) -> Dict:
    """
    Fetch benchmark index data for comparison

    Args:
        dry_run: If True, return mock data

    Returns:
        Dictionary with benchmark data
    """
    if dry_run:
        return {
            'SPY': {'price': 580.50, 'change_pct': 0.75, 'name': 'S&P 500'},
            'QQQ': {'price': 505.25, 'change_pct': 1.20, 'name': 'Nasdaq 100'},
            'IBB': {'price': 142.80, 'change_pct': 0.50, 'name': 'Biotech'},
            'IWM': {'price': 215.30, 'change_pct': 0.35, 'name': 'Russell 2000'}
        }

    try:
        api = tradeapi.REST(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )

        benchmarks = {}

        for symbol in BENCHMARKS.keys():
            try:
                # Get current quote
                snapshot = api.get_latest_trade(symbol)
                current_price = float(snapshot.price)

                # Get yesterday's close for daily change
                bars = api.get_bars(symbol, '1Day', limit=2).df
                if not bars.empty and len(bars) >= 2:
                    prev_close = float(bars['close'].iloc[-2])
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                else:
                    change_pct = 0.0

                benchmarks[symbol] = {
                    'price': current_price,
                    'change_pct': change_pct,
                    'name': BENCHMARKS[symbol]
                }

            except Exception as e:
                logging.warning(f"Failed to fetch benchmark {symbol}: {e}")

        return benchmarks

    except Exception as e:
        logging.error(f"Error fetching benchmarks: {e}")
        return {}


# ============================================================================
# PORTFOLIO DATA FETCHING
# ============================================================================

def fetch_portfolio_data(dry_run=False):
    """
    Fetch current portfolio data from Alpaca

    Args:
        dry_run: If True, return mock data for testing

    Returns:
        Dictionary with account and position data
    """
    if dry_run:
        print(f"{Colors.YELLOW}[DRY RUN MODE] Using mock data{Colors.RESET}\n")
        return get_mock_portfolio_data()

    try:
        api = tradeapi.REST(
            Config.ALPACA_API_KEY,
            Config.ALPACA_SECRET_KEY,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )

        account = api.get_account()
        positions = api.list_positions()

        portfolio = {
            'timestamp': datetime.now(),
            'account_status': account.status,
            'portfolio_value': float(account.portfolio_value),
            'cash': float(account.cash),
            'equity': float(account.equity),
            'last_equity': float(account.last_equity),
            'positions': []
        }

        for position in positions:
            portfolio['positions'].append({
                'symbol': position.symbol,
                'qty': float(position.qty),
                'side': position.side,
                'market_value': float(position.market_value),
                'cost_basis': float(position.cost_basis),
                'current_price': float(position.current_price),
                'avg_entry_price': float(position.avg_entry_price),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc)
            })

        return portfolio

    except Exception as e:
        print(f"{Colors.RED}Error fetching portfolio data: {e}{Colors.RESET}")
        return None


def get_mock_portfolio_data():
    """Return mock portfolio data for dry-run testing"""
    return {
        'timestamp': datetime.now(),
        'account_status': 'ACTIVE',
        'portfolio_value': 976.98,
        'cash': 374.41,
        'equity': 602.57,
        'last_equity': 550.00,
        'positions': [
            {'symbol': 'APLD', 'qty': 3, 'side': 'long', 'current_price': 38.14,
             'avg_entry_price': 21.58, 'market_value': 114.42, 'cost_basis': 64.74,
             'unrealized_pl': 49.68, 'unrealized_plpc': 0.7673},
            {'symbol': 'NTLA', 'qty': 6, 'side': 'long', 'current_price': 25.33,
             'avg_entry_price': 22.01, 'market_value': 151.98, 'cost_basis': 132.06,
             'unrealized_pl': 19.92, 'unrealized_plpc': 0.1509},
            {'symbol': 'SOUN', 'qty': 5, 'side': 'long', 'current_price': 19.00,
             'avg_entry_price': 16.08, 'market_value': 95.00, 'cost_basis': 80.40,
             'unrealized_pl': 14.60, 'unrealized_plpc': 0.1816},
            {'symbol': 'WYFI', 'qty': 2, 'side': 'long', 'current_price': 37.89,
             'avg_entry_price': 32.50, 'market_value': 75.78, 'cost_basis': 65.00,
             'unrealized_pl': 10.78, 'unrealized_plpc': 0.1658},
            {'symbol': 'TSSI', 'qty': 3, 'side': 'long', 'current_price': 18.90,
             'avg_entry_price': 17.30, 'market_value': 56.70, 'cost_basis': 51.90,
             'unrealized_pl': 4.80, 'unrealized_plpc': 0.0925},
            {'symbol': 'CRWV', 'qty': 0.77, 'side': 'long', 'current_price': 141.81,
             'avg_entry_price': 138.45, 'market_value': 109.19, 'cost_basis': 106.61,
             'unrealized_pl': 2.58, 'unrealized_plpc': 0.0242}
        ]
    }


# ============================================================================
# POSITION ANALYSIS AND ALERT DETECTION
# ============================================================================

def analyze_position_enhanced(position: Dict, target_config: Dict, market_data_mgr: Optional[MarketDataManager] = None) -> Dict:
    """
    Enhanced position analysis with additional API data

    Args:
        position: Position data from Alpaca
        target_config: Target configuration from POSITION_TARGETS
        market_data_mgr: Optional MarketDataManager for enhanced data

    Returns:
        Dictionary with comprehensive analysis results
    """
    # Get basic analysis first
    basic_analysis = analyze_position(position, target_config)

    # If no market data manager, return basic analysis
    if not market_data_mgr:
        return basic_analysis

    symbol = position['symbol']

    # Fetch enhanced data
    try:
        enhanced_data = market_data_mgr.get_enhanced_position_data(symbol)

        # Add technical indicators to analysis
        if enhanced_data.get('technical'):
            tech = enhanced_data['technical']

            # RSI signals
            if tech.get('rsi'):
                rsi_data = tech['rsi']
                basic_analysis['rsi'] = rsi_data.get('rsi')
                basic_analysis['rsi_oversold'] = rsi_data.get('oversold', False)
                basic_analysis['rsi_overbought'] = rsi_data.get('overbought', False)

            # MACD signals
            if tech.get('macd'):
                macd_data = tech['macd']
                basic_analysis['macd_signal'] = 'bullish' if macd_data.get('bullish_crossover') else 'bearish' if macd_data.get('bearish_crossover') else 'neutral'

        # Add news count
        if enhanced_data.get('news'):
            basic_analysis['news_count'] = enhanced_data['news'].get('count', 0)

        # Add sentiment
        if enhanced_data.get('sentiment'):
            sentiment = enhanced_data['sentiment']
            basic_analysis['sentiment_bullish'] = sentiment.get('bullish_pct', 0)
            basic_analysis['sentiment_bearish'] = sentiment.get('bearish_pct', 0)

        # Add SEC filings flag
        if enhanced_data.get('filings'):
            basic_analysis['recent_sec_filings'] = len(enhanced_data['filings']) > 0
            basic_analysis['sec_filing_count'] = len(enhanced_data['filings'])

    except Exception as e:
        logging.warning(f"Failed to fetch enhanced data for {symbol}: {e}")

    return basic_analysis


def analyze_position(position: Dict, target_config: Dict) -> Dict:
    """
    Analyze a single position against Project Oriana thresholds

    Args:
        position: Position data from Alpaca
        target_config: Target configuration from POSITION_TARGETS

    Returns:
        Dictionary with analysis results
    """
    symbol = position['symbol']
    current_price = position['current_price']
    qty = position['qty']

    # Use our tracked entry price, not Alpaca's average (which may include adds)
    entry_price = target_config['entry_price']

    # Calculate gain/loss from our tracked entry
    if entry_price:
        price_change = current_price - entry_price
        pct_change = (price_change / entry_price)
    else:
        pct_change = 0

    # Determine alert level
    alert_level = 'none'
    alert_type = None
    alert_message = ''
    action_required = False

    # Check gain thresholds
    if pct_change >= GAIN_THRESHOLDS['extreme']:
        alert_level = 'extreme'
        alert_type = 'gain'
        alert_message = f"+{pct_change*100:.1f}% gain - SELL 75% NOW"
        action_required = True
    elif pct_change >= GAIN_THRESHOLDS['critical']:
        alert_level = 'critical'
        alert_type = 'gain'
        alert_message = f"+{pct_change*100:.1f}% gain - SELL 50% to lock profits"
        action_required = True
    elif pct_change >= GAIN_THRESHOLDS['strong']:
        alert_level = 'strong'
        alert_type = 'gain'
        action_required = True
        # Calculate shares to sell for investment recovery
        shares_to_sell = calculate_shares_to_recover_investment(qty, entry_price, current_price)
        alert_message = f"+{pct_change*100:.1f}% gain - Sell {shares_to_sell} shares to recover investment"
    elif pct_change >= GAIN_THRESHOLDS['alert']:
        alert_level = 'alert'
        alert_type = 'gain'
        alert_message = f"+{pct_change*100:.1f}% gain - Monitor for profit-taking"

    # Check loss thresholds
    elif pct_change <= LOSS_THRESHOLDS['hard_stop']:
        alert_level = 'critical'
        alert_type = 'loss'
        alert_message = f"{pct_change*100:.1f}% loss - HARD STOP: SELL ALL {qty} SHARES NOW"
        action_required = True
    elif pct_change <= LOSS_THRESHOLDS['strong']:
        alert_level = 'strong'
        alert_type = 'loss'
        alert_message = f"{pct_change*100:.1f}% loss - Approaching hard stop, prepare exit"
        action_required = True
    elif pct_change <= LOSS_THRESHOLDS['alert']:
        alert_level = 'alert'
        alert_type = 'loss'
        alert_message = f"{pct_change*100:.1f}% loss - Review investment thesis"

    # Check if approaching thresholds (within 5%)
    approaching = []
    for threshold_name, threshold_value in {**GAIN_THRESHOLDS, **LOSS_THRESHOLDS}.items():
        if abs(pct_change - threshold_value) <= THRESHOLD_PROXIMITY:
            approaching.append((threshold_name, threshold_value))

    # Check if position size matches expected
    expected_qty = target_config['current_shares']
    qty_mismatch = abs(qty - expected_qty) > 0.01  # Allow tiny floating point differences

    return {
        'symbol': symbol,
        'entry_price': entry_price,
        'current_price': current_price,
        'qty': qty,
        'expected_qty': expected_qty,
        'qty_mismatch': qty_mismatch,
        'pct_change': pct_change,
        'alert_level': alert_level,
        'alert_type': alert_type,
        'alert_message': alert_message,
        'action_required': action_required,
        'approaching': approaching,
        'target_config': target_config
    }


def calculate_shares_to_recover_investment(qty: float, entry_price: float, current_price: float) -> int:
    """
    Calculate how many shares to sell to recover original investment

    For small positions (2-3 shares): sell 1 minimum
    For medium positions (5-7 shares): sell 30-50%
    For large positions (50+ shares): sell 40-50%
    """
    total_investment = qty * entry_price
    shares_to_sell = total_investment / current_price

    # Apply position-size based rules
    if qty <= 3:
        return max(1, int(shares_to_sell))
    elif qty <= 7:
        min_sell = int(qty * 0.30)
        max_sell = int(qty * 0.50)
        return max(min_sell, min(int(shares_to_sell), max_sell))
    else:
        min_sell = int(qty * 0.40)
        max_sell = int(qty * 0.50)
        return max(min_sell, min(int(shares_to_sell), max_sell))


def detect_position_changes(portfolio: Dict) -> Dict:
    """
    Detect unexpected position changes (new positions, completed adds, etc.)

    Returns:
        Dictionary with detected changes
    """
    changes = {
        'new_positions': [],
        'completed_adds': [],
        'unexpected_positions': [],
        'missing_positions': []
    }

    portfolio_symbols = {pos['symbol'] for pos in portfolio['positions']}
    expected_symbols = {sym for sym, cfg in POSITION_TARGETS.items()
                       if cfg['status'] != 'pending_new'}

    # Check for new positions
    for symbol in portfolio_symbols:
        if symbol not in POSITION_TARGETS:
            changes['unexpected_positions'].append(symbol)
        elif POSITION_TARGETS[symbol]['status'] == 'pending_new':
            changes['new_positions'].append(symbol)

    # Check for completed adds
    for pos in portfolio['positions']:
        symbol = pos['symbol']
        if symbol in POSITION_TARGETS:
            target = POSITION_TARGETS[symbol]
            if target['status'] == 'pending_add':
                if abs(pos['qty'] - target['target_shares']) < 0.1:
                    changes['completed_adds'].append(symbol)

    # Check for missing expected positions
    for symbol in expected_symbols:
        if symbol not in portfolio_symbols:
            changes['missing_positions'].append(symbol)

    return changes


# ============================================================================
# CLAUDE AI ANALYSIS
# ============================================================================

def get_claude_analysis(portfolio: Dict, analysis_data: List[Dict], dry_run=False) -> Optional[Tuple[str, Dict]]:
    """
    Get Claude AI analysis of portfolio positions

    Args:
        portfolio: Portfolio data
        analysis_data: List of position analyses
        dry_run: If True, skip Claude API call

    Returns:
        Tuple of (analysis_text, usage_stats) or None
    """
    if dry_run:
        return get_mock_claude_analysis(), {'input_tokens': 0, 'output_tokens': 0}

    try:
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # Build context for Claude
        positions_text = ""
        for analysis in analysis_data:
            pos = analysis
            positions_text += f"""
{pos['symbol']}:
  Entry: ${pos['entry_price']:.2f} → Current: ${pos['current_price']:.2f}
  Change: {pos['pct_change']*100:+.2f}%
  Shares: {pos['qty']:.2f} (target: {pos['expected_qty']:.2f})
  Alert: {pos['alert_message'] if pos['alert_message'] else 'None'}
"""

        prompt = f"""You are analyzing a microcap AI infrastructure portfolio using Project Oriana risk management.

Current Portfolio: ${portfolio['portfolio_value']:,.2f}
Cash Available: ${portfolio['cash']:,.2f}
Market Status: {"Open" if datetime.now().hour >= 9 and datetime.now().hour < 16 else "Closed"}

Positions:
{positions_text}

Provide brief analysis covering:
1. Any positions requiring IMMEDIATE action (hard stops or major profit-taking)
2. Market context for price moves in AI infrastructure sector
3. Recommended actions for approaching thresholds
4. Overall portfolio health assessment

Keep it concise and actionable. Focus on urgency and specific recommendations."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        usage = {
            'input_tokens': message.usage.input_tokens,
            'output_tokens': message.usage.output_tokens
        }

        return message.content[0].text, usage

    except Exception as e:
        print(f"{Colors.RED}Error getting Claude analysis: {e}{Colors.RESET}")
        return None, None


def get_mock_claude_analysis() -> str:
    """Return mock Claude analysis for dry-run mode"""
    return """[MOCK ANALYSIS - DRY RUN MODE]

1. IMMEDIATE ACTIONS:
   - APLD at +76.7%: Approaching +100% critical threshold. Consider taking partial profits.

2. MARKET CONTEXT:
   - AI infrastructure stocks showing strength
   - Momentum continues in semiconductor/AI plays

3. RECOMMENDATIONS:
   - APLD: Monitor closely, prepare to sell 1-2 shares at +100%
   - NTLA, SOUN, WYFI: Strong gains, hold for now
   - TSSI, CRWV: Steady, continue monitoring

4. PORTFOLIO HEALTH: STRONG
   - All positions profitable
   - No loss alerts triggered
   - Good sector concentration in AI/tech"""


# ============================================================================
# REPORT GENERATION
# ============================================================================

def print_morning_brief(portfolio: Dict, analysis_data: List[Dict],
                       changes: Dict, claude_analysis: Optional[str],
                       usage: Optional[Dict], benchmarks: Optional[Dict] = None):
    """Generate and print the morning portfolio brief"""

    # Header
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"  PROJECT ORIANA - PORTFOLIO MONITORING BRIEF")
    print(f"  {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"{'='*80}{Colors.RESET}\n")

    # Benchmarks (if provided)
    if benchmarks:
        print(f"{Colors.BOLD}📈 MARKET BENCHMARKS{Colors.RESET}")
        print(f"{'─'*80}")
        for symbol, data in benchmarks.items():
            change_color = Colors.GREEN if data['change_pct'] >= 0 else Colors.RED
            print(f"{data['name']:20s} ${data['price']:>7.2f}  {change_color}{data['change_pct']:>+6.2f}%{Colors.RESET}")
        print()

    # Portfolio Status
    print(f"{Colors.BOLD}📊 PORTFOLIO STATUS{Colors.RESET}")
    print(f"{'─'*80}")

    total_value = portfolio['portfolio_value']
    cash = portfolio['cash']
    equity = portfolio['equity']
    last_equity = portfolio['last_equity']
    daily_change = equity - last_equity
    daily_change_pct = (daily_change / last_equity * 100) if last_equity > 0 else 0

    # Calculate portfolio completion
    total_target = sum(cfg['target_value'] for cfg in POSITION_TARGETS.values())
    current_deployed = sum(pos['market_value'] for pos in portfolio['positions'])
    completion_pct = (current_deployed / total_target * 100) if total_target > 0 else 0

    # Calculate total portfolio performance vs initial investment
    total_gain = total_value - INITIAL_INVESTMENT
    total_gain_pct = (total_gain / INITIAL_INVESTMENT * 100) if INITIAL_INVESTMENT > 0 else 0

    change_color = Colors.GREEN if daily_change >= 0 else Colors.RED
    gain_color = Colors.GREEN if total_gain >= 0 else Colors.RED

    print(f"Total Value: {Colors.BOLD}${total_value:,.2f}{Colors.RESET}")
    print(f"Initial Investment: ${INITIAL_INVESTMENT:,.2f}")
    print(f"Total Gain/Loss: {gain_color}${total_gain:+,.2f} ({total_gain_pct:+.2f}%){Colors.RESET}")
    print(f"Today's Change: {change_color}${daily_change:+.2f} ({daily_change_pct:+.2f}%){Colors.RESET}")
    print(f"Cash Available: ${cash:,.2f}")
    print(f"Portfolio Completion: {completion_pct:.1f}%")
    print()

    # Profit Opportunities
    profit_alerts = [a for a in analysis_data if a['alert_type'] == 'gain' and a['alert_level'] != 'none']
    if profit_alerts:
        print(f"{Colors.BOLD}{Colors.GREEN}🟢 PROFIT OPPORTUNITIES{Colors.RESET}")
        print(f"{'─'*80}")
        for alert in sorted(profit_alerts, key=lambda x: x['pct_change'], reverse=True):
            urgency = "🔥 " if alert['action_required'] else ""
            print(f"{urgency}{alert['symbol']}: {alert['alert_message']}")
        print()

    # Risk Alerts
    loss_alerts = [a for a in analysis_data if a['alert_type'] == 'loss']
    if loss_alerts:
        print(f"{Colors.BOLD}{Colors.RED}🔴 RISK ALERTS{Colors.RESET}")
        print(f"{'─'*80}")
        for alert in sorted(loss_alerts, key=lambda x: x['pct_change']):
            urgency = "⚠️  " if alert['action_required'] else ""
            print(f"{urgency}{alert['symbol']}: {alert['alert_message']}")
        print()

    # Approaching Thresholds
    approaching = [a for a in analysis_data if a['approaching']]
    if approaching:
        print(f"{Colors.BOLD}{Colors.YELLOW}⚠️  APPROACHING THRESHOLDS{Colors.RESET}")
        print(f"{'─'*80}")
        for alert in approaching:
            for threshold_name, threshold_value in alert['approaching']:
                print(f"{alert['symbol']}: Within 5% of {threshold_name} threshold ({threshold_value*100:+.0f}%)")
        print()

    # Position Changes
    if any(changes.values()):
        print(f"{Colors.BOLD}{Colors.MAGENTA}🔄 POSITION CHANGES DETECTED{Colors.RESET}")
        print(f"{'─'*80}")
        if changes['new_positions']:
            print(f"✨ New positions: {', '.join(changes['new_positions'])}")
        if changes['completed_adds']:
            print(f"✅ Completed adds: {', '.join(changes['completed_adds'])}")
        if changes['unexpected_positions']:
            print(f"❓ Unexpected positions: {', '.join(changes['unexpected_positions'])}")
        if changes['missing_positions']:
            print(f"❌ Missing positions: {', '.join(changes['missing_positions'])}")
        print()

    # Action Items
    action_items = [a for a in analysis_data if a['action_required']]
    print(f"{Colors.BOLD}💰 ACTION ITEMS TODAY{Colors.RESET}")
    print(f"{'─'*80}")
    if action_items:
        for idx, item in enumerate(action_items, 1):
            print(f"{idx}. {item['symbol']}: {item['alert_message']}")
    else:
        print("No immediate actions required. Continue monitoring.")
    print()

    # Rebalancing Status
    print(f"{Colors.BOLD}📅 REBALANCING STATUS{Colors.RESET}")
    print(f"{'─'*80}")
    for symbol, config in POSITION_TARGETS.items():
        status_icon = {
            'complete': '✓',
            'trimmed': '✓',
            'pending_add': '⏳',
            'pending_new': '⏳'
        }.get(config['status'], '?')

        status_text = config['notes']
        print(f"{status_icon} {symbol}: {status_text}")
    print()

    # Claude Analysis
    if claude_analysis:
        print(f"{Colors.BOLD}🤖 AI ANALYSIS{Colors.RESET}")
        print(f"{'─'*80}")
        print(claude_analysis)
        print()

    # API Usage
    if usage:
        input_cost = (usage['input_tokens'] / 1_000_000) * 3.00
        output_cost = (usage['output_tokens'] / 1_000_000) * 15.00
        total_cost = input_cost + output_cost
        print(f"{Colors.BOLD}📊 API Usage{Colors.RESET}")
        print(f"Tokens: {usage['input_tokens']} in / {usage['output_tokens']} out")
        print(f"Cost: ${total_cost:.4f}")
        print()

    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")


# ============================================================================
# MARKET CLOSE SUMMARY
# ============================================================================

def generate_market_close_summary(portfolio: Dict, analysis_data: List[Dict],
                                  morning_snapshot: Optional[Dict] = None) -> Dict:
    """
    Generate comprehensive end-of-day market close summary

    Args:
        portfolio: Current portfolio data
        analysis_data: Position analysis data
        morning_snapshot: Optional morning portfolio data for comparison

    Returns:
        Dictionary with structured summary data
    """
    from pathlib import Path
    import re

    summary = {
        'timestamp': datetime.now(),
        'daily_performance': {},
        'alerts_triggered': [],
        'position_changes': {},
        'rebalancing_status': {},
        'tomorrows_watchlist': [],
        'cost_tracking': {}
    }

    # 1. DAILY PERFORMANCE
    total_value = portfolio['portfolio_value']
    equity = portfolio['equity']
    last_equity = portfolio['last_equity']
    daily_change = equity - last_equity
    daily_change_pct = (daily_change / last_equity * 100) if last_equity > 0 else 0

    # Find best and worst performers
    performers = []
    green_count = 0
    red_count = 0

    for analysis in analysis_data:
        pct_change = analysis['pct_change'] * 100
        performers.append({
            'symbol': analysis['symbol'],
            'pct_change': pct_change
        })
        if pct_change >= 0:
            green_count += 1
        else:
            red_count += 1

    performers.sort(key=lambda x: x['pct_change'], reverse=True)

    summary['daily_performance'] = {
        'open_value': last_equity,
        'close_value': equity,
        'total_change': daily_change,
        'total_change_pct': daily_change_pct,
        'best_performer': performers[0] if performers else None,
        'worst_performer': performers[-1] if performers else None,
        'green_positions': green_count,
        'red_positions': red_count
    }

    # 2. ALERTS TRIGGERED TODAY
    log_file = Path('logs') / f"monitoring_{datetime.now().strftime('%Y-%m-%d')}.log"
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()

            # Parse alerts from log
            alert_pattern = r'NEW ALERT: (\S+) - (.+)'
            alerts = re.findall(alert_pattern, log_content)

            for alert_key, message in alerts:
                # Categorize alert
                if 'gain' in message.lower() or '+' in message:
                    category = 'profit'
                elif 'loss' in message.lower() or 'stop' in message.lower():
                    category = 'risk'
                else:
                    category = 'informational'

                action_required = 'SELL' in message.upper() or 'IMMEDIATE' in message.upper()

                summary['alerts_triggered'].append({
                    'alert_key': alert_key,
                    'message': message,
                    'category': category,
                    'action_required': action_required
                })
        except Exception as e:
            logging.warning(f"Could not read log file: {e}")

    # 3. POSITION CHANGES DETECTED
    if morning_snapshot:
        morning_symbols = {pos['symbol']: pos for pos in morning_snapshot.get('positions', [])}
        current_symbols = {pos['symbol']: pos for pos in portfolio['positions']}

        changes = {
            'shares_added': [],
            'shares_removed': [],
            'positions_opened': [],
            'positions_closed': []
        }

        # Check for new positions
        for symbol in current_symbols:
            if symbol not in morning_symbols:
                changes['positions_opened'].append(symbol)
            elif current_symbols[symbol]['qty'] > morning_symbols[symbol]['qty']:
                qty_added = current_symbols[symbol]['qty'] - morning_symbols[symbol]['qty']
                changes['shares_added'].append({
                    'symbol': symbol,
                    'qty': qty_added
                })
            elif current_symbols[symbol]['qty'] < morning_symbols[symbol]['qty']:
                qty_removed = morning_symbols[symbol]['qty'] - current_symbols[symbol]['qty']
                changes['shares_removed'].append({
                    'symbol': symbol,
                    'qty': qty_removed
                })

        # Check for closed positions
        for symbol in morning_symbols:
            if symbol not in current_symbols:
                changes['positions_closed'].append(symbol)

        summary['position_changes'] = changes

    # 4. PORTFOLIO REBALANCING STATUS
    total_target = sum(cfg['target_value'] for cfg in POSITION_TARGETS.values())
    current_deployed = sum(pos['market_value'] for pos in portfolio['positions'])
    completion_pct = (current_deployed / total_target * 100) if total_target > 0 else 0

    capital_needed = 0
    for symbol, config in POSITION_TARGETS.items():
        if config['status'] in ['pending_add', 'pending_new']:
            # Estimate capital needed
            current_pos = next((p for p in portfolio['positions'] if p['symbol'] == symbol), None)
            if current_pos:
                avg_price = current_pos['current_price']
                shares_needed = config['target_shares'] - config['current_shares']
                capital_needed += avg_price * shares_needed
            else:
                capital_needed += config['target_value']

    summary['rebalancing_status'] = {
        'completion_pct': completion_pct,
        'capital_needed': capital_needed,
        'cash_available': portfolio['cash'],
        'positions_at_target': len([c for c in POSITION_TARGETS.values() if c['status'] in ['complete', 'trimmed']]),
        'positions_pending': len([c for c in POSITION_TARGETS.values() if c['status'] in ['pending_add', 'pending_new']])
    }

    # 5. TOMORROW'S WATCHLIST
    watchlist = []
    for analysis in analysis_data:
        pct = analysis['pct_change']
        symbol = analysis['symbol']

        # Check proximity to thresholds
        gain_thresholds = [0.25, 0.50, 1.00]  # +25%, +50%, +100%
        loss_thresholds = [-0.10, -0.15, -0.20]  # -10%, -15%, -20%

        for threshold in gain_thresholds + loss_thresholds:
            if abs(pct - threshold) <= 0.05:  # Within 5%
                watchlist.append({
                    'symbol': symbol,
                    'current_pct': pct * 100,
                    'threshold': threshold * 100,
                    'threshold_name': f"{'+' if threshold > 0 else ''}{int(threshold*100)}%",
                    'distance': abs(pct - threshold) * 100
                })

    # Add pending adds to watchlist
    for symbol, config in POSITION_TARGETS.items():
        if config['status'] in ['pending_add', 'pending_new']:
            watchlist.append({
                'symbol': symbol,
                'action': 'pending_add' if config['status'] == 'pending_add' else 'pending_new',
                'shares_needed': config['pending_add'],
                'notes': config['notes']
            })

    summary['tomorrows_watchlist'] = watchlist

    # 6. COST TRACKING
    # Parse API usage from logs
    api_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0

    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()

            # Count API calls (look for "Getting AI analysis" or similar)
            api_calls = log_content.count('Getting AI analysis') + log_content.count('Sending portfolio to Claude')

            # Try to extract token usage (if logged)
            token_pattern = r'(\d+) in / (\d+) out'
            token_matches = re.findall(token_pattern, log_content)
            for inp, out in token_matches:
                total_input_tokens += int(inp)
                total_output_tokens += int(out)

        except Exception as e:
            logging.warning(f"Could not parse API usage: {e}")

    # Calculate costs (Claude Sonnet 4.5 pricing)
    input_cost = (total_input_tokens / 1_000_000) * 3.00
    output_cost = (total_output_tokens / 1_000_000) * 15.00
    daily_cost = input_cost + output_cost

    # Estimate monthly cost (assuming 21 trading days)
    monthly_estimate = daily_cost * 21

    summary['cost_tracking'] = {
        'api_calls_today': api_calls,
        'input_tokens': total_input_tokens,
        'output_tokens': total_output_tokens,
        'daily_cost': daily_cost,
        'monthly_estimate': monthly_estimate
    }

    return summary


def print_market_close_summary(summary: Dict):
    """Print formatted market close summary"""

    # Header
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"  PROJECT ORIANA - MARKET CLOSE SUMMARY")
    print(f"  {summary['timestamp'].strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"{'='*80}{Colors.RESET}\n")

    # 1. DAILY PERFORMANCE
    perf = summary['daily_performance']
    print(f"{Colors.BOLD}📈 DAILY PERFORMANCE{Colors.RESET}")
    print(f"{'─'*80}")

    change_color = Colors.GREEN if perf['total_change'] >= 0 else Colors.RED
    print(f"Market Open:  ${perf['open_value']:,.2f}")
    print(f"Market Close: ${perf['close_value']:,.2f}")
    print(f"Daily Change: {change_color}${perf['total_change']:+,.2f} ({perf['total_change_pct']:+.2f}%){Colors.RESET}")
    print()

    if perf['best_performer']:
        best = perf['best_performer']
        print(f"🏆 Best Performer:  {best['symbol']} ({best['pct_change']:+.2f}%)")

    if perf['worst_performer']:
        worst = perf['worst_performer']
        print(f"📉 Worst Performer: {worst['symbol']} ({worst['pct_change']:+.2f}%)")

    print(f"\nPositions: {Colors.GREEN}{perf['green_positions']} up{Colors.RESET} | "
          f"{Colors.RED}{perf['red_positions']} down{Colors.RESET}")
    print()

    # 2. ALERTS TRIGGERED TODAY
    if summary['alerts_triggered']:
        print(f"{Colors.BOLD}🚨 ALERTS TRIGGERED TODAY ({len(summary['alerts_triggered'])}){Colors.RESET}")
        print(f"{'─'*80}")

        # Group by category
        profit_alerts = [a for a in summary['alerts_triggered'] if a['category'] == 'profit']
        risk_alerts = [a for a in summary['alerts_triggered'] if a['category'] == 'risk']
        info_alerts = [a for a in summary['alerts_triggered'] if a['category'] == 'informational']

        if profit_alerts:
            print(f"\n{Colors.GREEN}Profit Opportunities:{Colors.RESET}")
            for alert in profit_alerts:
                action = " [ACTION REQUIRED]" if alert['action_required'] else ""
                print(f"  • {alert['alert_key']}: {alert['message']}{action}")

        if risk_alerts:
            print(f"\n{Colors.RED}Risk Alerts:{Colors.RESET}")
            for alert in risk_alerts:
                action = " [ACTION REQUIRED]" if alert['action_required'] else ""
                print(f"  • {alert['alert_key']}: {alert['message']}{action}")

        if info_alerts:
            print(f"\n{Colors.CYAN}Informational:{Colors.RESET}")
            for alert in info_alerts:
                print(f"  • {alert['alert_key']}: {alert['message']}")

        print()

    # 3. POSITION CHANGES DETECTED
    if summary.get('position_changes'):
        changes = summary['position_changes']
        if any(changes.values()):
            print(f"{Colors.BOLD}🔄 POSITION CHANGES DETECTED{Colors.RESET}")
            print(f"{'─'*80}")

            if changes['positions_opened']:
                print(f"✨ New Positions Opened: {', '.join(changes['positions_opened'])}")

            if changes['shares_added']:
                print(f"➕ Shares Added:")
                for item in changes['shares_added']:
                    print(f"  • {item['symbol']}: +{item['qty']} shares")

            if changes['shares_removed']:
                print(f"➖ Shares Removed:")
                for item in changes['shares_removed']:
                    print(f"  • {item['symbol']}: -{item['qty']} shares")

            if changes['positions_closed']:
                print(f"🔒 Positions Closed: {', '.join(changes['positions_closed'])}")

            print()

    # 4. PORTFOLIO REBALANCING STATUS
    rebal = summary['rebalancing_status']
    print(f"{Colors.BOLD}📊 PORTFOLIO REBALANCING STATUS{Colors.RESET}")
    print(f"{'─'*80}")
    print(f"Completion: {rebal['completion_pct']:.1f}%")
    print(f"At Target: {rebal['positions_at_target']} positions")
    print(f"Pending: {rebal['positions_pending']} positions")
    print(f"Capital Needed: ${rebal['capital_needed']:,.2f}")
    print(f"Cash Available: ${rebal['cash_available']:,.2f}")

    if rebal['capital_needed'] <= rebal['cash_available']:
        print(f"{Colors.GREEN}✓ Sufficient cash for pending adds{Colors.RESET}")
    else:
        shortfall = rebal['capital_needed'] - rebal['cash_available']
        print(f"{Colors.YELLOW}⚠ Need ${shortfall:,.2f} more for full rebalancing{Colors.RESET}")
    print()

    # 5. TOMORROW'S WATCHLIST
    if summary['tomorrows_watchlist']:
        print(f"{Colors.BOLD}👀 TOMORROW'S WATCHLIST{Colors.RESET}")
        print(f"{'─'*80}")

        threshold_items = [w for w in summary['tomorrows_watchlist'] if 'threshold' in w]
        action_items = [w for w in summary['tomorrows_watchlist'] if 'action' in w]

        if threshold_items:
            print(f"\nApproaching Thresholds:")
            for item in threshold_items:
                print(f"  • {item['symbol']}: {item['current_pct']:.1f}% "
                      f"(within {item['distance']:.1f}% of {item['threshold_name']})")

        if action_items:
            print(f"\nPending Actions:")
            for item in action_items:
                if item['action'] == 'pending_add':
                    print(f"  ⏳ {item['symbol']}: Add {item['shares_needed']} shares")
                else:
                    print(f"  ✨ {item['symbol']}: Open new position ({item['shares_needed']} shares)")

        print()

    # 6. COST TRACKING
    cost = summary['cost_tracking']
    print(f"{Colors.BOLD}💰 API COST TRACKING{Colors.RESET}")
    print(f"{'─'*80}")
    print(f"API Calls Today: {cost['api_calls_today']}")
    print(f"Tokens: {cost['input_tokens']:,} in / {cost['output_tokens']:,} out")
    print(f"Today's Cost: ${cost['daily_cost']:.4f}")
    print(f"Monthly Estimate: ${cost['monthly_estimate']:.2f} (@ 21 trading days)")
    print()

    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")

    return summary


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_monitoring_agent(dry_run=False, send_email=False):
    """
    Main monitoring agent execution

    Args:
        dry_run: If True, use mock data and skip API calls
        send_email: If True, send email alerts for critical events
    """
    try:
        # Validate configuration (skip for dry run)
        if not dry_run:
            print("Validating configuration...")
            Config.validate()
            print(f"{Colors.GREEN}Configuration validated!{Colors.RESET}\n")

        # Fetch portfolio data
        print("Fetching portfolio data...")
        portfolio = fetch_portfolio_data(dry_run=dry_run)

        if not portfolio:
            print(f"{Colors.RED}Failed to fetch portfolio data{Colors.RESET}")
            return False

        print(f"{Colors.GREEN}Portfolio data retrieved!{Colors.RESET}\n")

        # Analyze each position
        analysis_data = []
        for position in portfolio['positions']:
            symbol = position['symbol']
            if symbol in POSITION_TARGETS:
                analysis = analyze_position(position, POSITION_TARGETS[symbol])
                analysis_data.append(analysis)

        # Detect position changes
        changes = detect_position_changes(portfolio)

        # Fetch benchmark data
        print("Fetching market benchmarks...")
        benchmarks = fetch_benchmark_data(dry_run=dry_run)

        # Get Claude analysis
        claude_analysis = None
        usage = None
        if not dry_run:
            print("Getting AI analysis...")
            claude_analysis, usage = get_claude_analysis(portfolio, analysis_data, dry_run=dry_run)
        else:
            claude_analysis, usage = get_claude_analysis(portfolio, analysis_data, dry_run=True)

        # Generate morning brief
        print_morning_brief(portfolio, analysis_data, changes, claude_analysis, usage, benchmarks)

        # Send email alerts if requested
        if send_email and not dry_run:
            try:
                from email_alerts import EmailAlertSystem

                email_system = EmailAlertSystem()

                # Send critical alerts if any
                critical_alerts = [pos for pos in analysis_data if pos['action_required']]

                if critical_alerts:
                    print(f"\n{Colors.CYAN}Sending email alerts...{Colors.RESET}")
                    success = email_system.send_critical_alerts(analysis_data, portfolio['portfolio_value'])

                    if success:
                        print(f"{Colors.GREEN}✓ Email alerts sent{Colors.RESET}\n")
                    else:
                        print(f"{Colors.YELLOW}⚠ Failed to send email alerts{Colors.RESET}\n")

            except ImportError:
                print(f"{Colors.YELLOW}⚠ Email alert system not available{Colors.RESET}\n")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠ Email error: {e}{Colors.RESET}\n")
                logging.error(f"Email error: {e}", exc_info=True)

        return True

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Monitoring stopped by user{Colors.RESET}")
        return False
    except Exception as e:
        print(f"\n{Colors.RED}Error in monitoring agent: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Project Oriana Portfolio Monitoring Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitoring_agent.py                    # Run once with live data
  python monitoring_agent.py --once             # Run once (explicit)
  python monitoring_agent.py --morning          # Generate morning brief
  python monitoring_agent.py --morning --email  # Morning brief with email
  python monitoring_agent.py --monitor          # Continuous monitoring (every 5 min)
  python monitoring_agent.py --close            # Market close summary (4:15 PM)
  python monitoring_agent.py --dry-run          # Test with mock data
  python monitoring_agent.py --monitor --debug  # Monitor with debug logging
        """
    )

    # Monitoring modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (default behavior)'
    )
    mode_group.add_argument(
        '--monitor',
        action='store_true',
        help='Run continuously every 5 minutes during market hours'
    )
    mode_group.add_argument(
        '--close',
        action='store_true',
        help='Generate market close summary (run at 4:15 PM)'
    )
    mode_group.add_argument(
        '--morning',
        action='store_true',
        help='Generate morning brief with overnight developments'
    )

    # Options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode with mock data (no API calls)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--email',
        action='store_true',
        help='Send email alerts for critical events'
    )

    args = parser.parse_args()

    # Determine mode
    if args.morning:
        # Generate morning brief
        import morning_brief
        success = morning_brief.run_morning_brief(
            dry_run=args.dry_run,
            send_email=args.email
        )
    elif args.monitor or args.close:
        # Import continuous monitoring module
        import continuous_monitor

        # Setup logging
        setup_logging(debug=args.debug)

        # Run continuous monitoring
        mode = 'close' if args.close else 'monitor'
        success = continuous_monitor.run_continuous_monitor(
            mode=mode,
            dry_run=args.dry_run,
            debug=args.debug,
            send_email=args.email
        )
    else:
        # Default: run once
        if args.debug:
            setup_logging(debug=True)

        success = run_monitoring_agent(dry_run=args.dry_run, send_email=args.email)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
