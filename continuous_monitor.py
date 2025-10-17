"""
Continuous Monitoring Module for Portfolio Monitoring Agent
Handles continuous monitoring loop, market hours checking, and alert deduplication
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional
import monitoring_agent as agent


def run_continuous_monitor(mode: str = 'monitor', dry_run: bool = False, debug: bool = False, send_email: bool = False):
    """
    Run continuous monitoring loop

    Args:
        mode: 'monitor' (continuous) or 'close' (market close summary)
        dry_run: Use mock data
        debug: Enable debug logging
        send_email: Send email alerts

    Returns:
        Boolean success status
    """
    # Setup logging
    agent.setup_logging(debug=debug)
    logging.info(f"Starting continuous monitor in {mode} mode")

    # Initialize monitoring state
    agent.monitoring_state.start_time = datetime.now()
    agent.monitoring_state.reset_for_new_day()

    if mode == 'close':
        return run_close_summary(dry_run=dry_run, send_email=send_email)
    else:
        return run_monitoring_loop(dry_run=dry_run, send_email=send_email)


def run_monitoring_loop(dry_run: bool = False, send_email: bool = False):
    """
    Continuous monitoring loop - runs every 5 minutes during market hours

    Args:
        dry_run: Use mock data
        send_email: Send email alerts for critical events
    """
    print(f"\n{agent.Colors.BOLD}{agent.Colors.CYAN}{'='*80}")
    print("  PROJECT ORIANA - CONTINUOUS MONITORING MODE")
    print("  Press Ctrl+C to stop")
    print(f"{'='*80}{agent.Colors.RESET}\n")

    check_interval = 300  # 5 minutes in seconds

    try:
        while not agent.monitoring_state.shutdown_requested:
            # Reset alert tracking for new day
            agent.monitoring_state.reset_for_new_day()

            # Check market status
            is_open, next_open, next_close, clock = agent.check_market_status(dry_run=dry_run)

            if not is_open:
                print(f"\n{agent.Colors.YELLOW}Market is closed.{agent.Colors.RESET}")
                if next_open:
                    print(f"Next open: {next_open}")

                # Calculate time until market opens
                if next_open and not dry_run:
                    wait_time = (next_open - datetime.now(next_open.tzinfo)).total_seconds()
                    if wait_time > 0:
                        print(f"Waiting until market opens (sleeping for {wait_time/3600:.1f} hours)...")
                        logging.info(f"Market closed, waiting {wait_time/3600:.1f} hours until open")

                        # Sleep in chunks to allow Ctrl+C
                        while wait_time > 0 and not agent.monitoring_state.shutdown_requested:
                            sleep_chunk = min(60, wait_time)  # Sleep max 60 seconds at a time
                            time.sleep(sleep_chunk)
                            wait_time -= sleep_chunk
                        continue
                else:
                    # Dry run or no next open time - just sleep and retry
                    time.sleep(60)
                    continue

            # Market is open - perform check
            print(f"\n{agent.Colors.GREEN}Market is open - Running portfolio check #{agent.monitoring_state.checks_performed + 1}{agent.Colors.RESET}")
            logging.info(f"Performing portfolio check #{agent.monitoring_state.checks_performed + 1}")

            try:
                # Run full monitoring analysis
                success = run_single_check(dry_run=dry_run, monitor_mode=True, send_email=send_email)

                if success:
                    agent.monitoring_state.checks_performed += 1
                else:
                    logging.warning("Portfolio check failed, will retry next interval")

            except Exception as e:
                logging.error(f"Error during portfolio check: {e}", exc_info=True)
                print(f"{agent.Colors.RED}Error during check: {e}{agent.Colors.RESET}")

            # Check if market is closing soon
            if next_close and not dry_run:
                time_to_close = (next_close - datetime.now(next_close.tzinfo)).total_seconds()
                if time_to_close < check_interval:
                    print(f"\n{agent.Colors.YELLOW}Market closing soon, waiting until close...{agent.Colors.RESET}")
                    if time_to_close > 0:
                        time.sleep(time_to_close + 60)  # Wait until after close
                    continue

            # Sleep until next check
            if not agent.monitoring_state.shutdown_requested:
                print(f"\n{agent.Colors.CYAN}Next check in 5 minutes...{agent.Colors.RESET}")
                logging.info(f"Sleeping for {check_interval} seconds")

                # Sleep in chunks to allow Ctrl+C
                remaining = check_interval
                while remaining > 0 and not agent.monitoring_state.shutdown_requested:
                    sleep_chunk = min(10, remaining)
                    time.sleep(sleep_chunk)
                    remaining -= sleep_chunk

        # Graceful shutdown
        print(f"\n{agent.Colors.CYAN}{'='*80}")
        print(f"  MONITORING SESSION SUMMARY")
        print(f"{'='*80}{agent.Colors.RESET}")
        print(f"\n{agent.monitoring_state.get_summary()}")
        print(f"\n{agent.Colors.GREEN}Monitoring stopped gracefully.{agent.Colors.RESET}\n")
        logging.info("Monitoring stopped gracefully")
        logging.info(agent.monitoring_state.get_summary())

        return True

    except Exception as e:
        logging.error(f"Fatal error in monitoring loop: {e}", exc_info=True)
        print(f"\n{agent.Colors.RED}Fatal error: {e}{agent.Colors.RESET}")
        return False


def run_single_check(dry_run: bool = False, monitor_mode: bool = False, send_email: bool = False) -> bool:
    """
    Run a single portfolio check

    Args:
        dry_run: Use mock data
        monitor_mode: If True, only show new alerts (deduplicate)
        send_email: Send email alerts for critical events

    Returns:
        Boolean success status
    """
    try:
        # Fetch portfolio data
        portfolio = agent.fetch_portfolio_data(dry_run=dry_run)
        if not portfolio:
            return False

        # Analyze each position
        analysis_data = []
        new_alerts = []

        for position in portfolio['positions']:
            symbol = position['symbol']
            if symbol in agent.POSITION_TARGETS:
                analysis = agent.analyze_position(position, agent.POSITION_TARGETS[symbol])
                analysis_data.append(analysis)

                # Check for new alerts in monitor mode
                if monitor_mode and analysis['action_required']:
                    alert_key = f"{symbol}_{analysis['alert_level']}"

                    if not agent.monitoring_state.has_sent_alert(alert_key):
                        new_alerts.append(analysis)
                        agent.monitoring_state.mark_alert_sent(alert_key)
                        logging.info(f"NEW ALERT: {alert_key} - {analysis['alert_message']}")

        # Detect position changes
        changes = agent.detect_position_changes(portfolio)

        # Get Claude analysis (skip in monitor mode unless there are new alerts)
        claude_analysis = None
        usage = None

        if not monitor_mode or new_alerts or any(changes.values()):
            if not dry_run:
                claude_analysis, usage = agent.get_claude_analysis(
                    portfolio, analysis_data, dry_run=dry_run
                )
            else:
                claude_analysis, usage = agent.get_claude_analysis(
                    portfolio, analysis_data, dry_run=True
                )

        # In monitor mode, only print if there are new alerts or changes
        if monitor_mode:
            if new_alerts or any(changes.values()):
                print(f"\n{agent.Colors.BOLD}{agent.Colors.RED}🚨 NEW ALERTS DETECTED 🚨{agent.Colors.RESET}")
                agent.print_morning_brief(portfolio, analysis_data, changes, claude_analysis, usage)

                # Send email for new critical alerts
                if send_email and new_alerts and not dry_run:
                    try:
                        from email_alerts import EmailAlertSystem
                        email_system = EmailAlertSystem()

                        print(f"\n{agent.Colors.CYAN}Sending email alerts...{agent.Colors.RESET}")
                        success = email_system.send_critical_alerts(new_alerts, portfolio['portfolio_value'])

                        if success:
                            print(f"{agent.Colors.GREEN}✓ Email alerts sent{agent.Colors.RESET}\n")
                        else:
                            print(f"{agent.Colors.YELLOW}⚠ Failed to send email alerts{agent.Colors.RESET}\n")
                    except Exception as e:
                        logging.error(f"Email error: {e}", exc_info=True)

            else:
                # Just show quick status
                print(f"  Portfolio: ${portfolio['portfolio_value']:,.2f} | "
                      f"Positions: {len(portfolio['positions'])} | "
                      f"All quiet - no new alerts")
        else:
            # Full report for non-monitor mode
            agent.print_morning_brief(portfolio, analysis_data, changes, claude_analysis, usage)

        return True

    except Exception as e:
        logging.error(f"Error in single check: {e}", exc_info=True)
        return False


def run_close_summary(dry_run: bool = False, send_email: bool = False) -> bool:
    """
    Generate comprehensive market close summary at 4:15 PM

    Args:
        dry_run: Use mock data
        send_email: Send daily summary email
    """
    # Check if it's actually after market close
    is_open, next_open, next_close, clock = agent.check_market_status(dry_run=dry_run)

    if is_open and not dry_run:
        print(f"\n{agent.Colors.YELLOW}Warning: Market is still open!{agent.Colors.RESET}")
        print("Market close summary should be run after 4:00 PM ET\n")

    logging.info("Generating market close summary")

    try:
        # Fetch portfolio data
        portfolio = agent.fetch_portfolio_data(dry_run=dry_run)
        if not portfolio:
            print(f"{agent.Colors.RED}Failed to fetch portfolio data{agent.Colors.RESET}")
            return False

        # Analyze each position
        analysis_data = []
        for position in portfolio['positions']:
            symbol = position['symbol']
            if symbol in agent.POSITION_TARGETS:
                analysis = agent.analyze_position(position, agent.POSITION_TARGETS[symbol])
                analysis_data.append(analysis)

        # Generate comprehensive summary
        summary = agent.generate_market_close_summary(
            portfolio=portfolio,
            analysis_data=analysis_data,
            morning_snapshot=None  # TODO: Could load from saved morning snapshot
        )

        # Print formatted summary
        agent.print_market_close_summary(summary)

        # Save summary to file for record keeping
        from pathlib import Path
        import json

        summary_dir = Path('summaries')
        summary_dir.mkdir(exist_ok=True)

        summary_file = summary_dir / f"close_summary_{datetime.now().strftime('%Y-%m-%d')}.json"

        # Convert datetime objects to strings for JSON serialization
        json_summary = summary.copy()
        json_summary['timestamp'] = summary['timestamp'].isoformat()

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(json_summary, f, indent=2)

        logging.info(f"Market close summary saved to {summary_file}")
        print(f"{agent.Colors.GREEN}Summary saved to: {summary_file}{agent.Colors.RESET}\n")

        # Send email summary if requested
        if send_email and not dry_run:
            try:
                from email_alerts import EmailAlertSystem
                email_system = EmailAlertSystem()

                print(f"{agent.Colors.CYAN}Sending daily summary email...{agent.Colors.RESET}")
                success = email_system.send_daily_summary(summary)

                if success:
                    print(f"{agent.Colors.GREEN}✓ Daily summary email sent{agent.Colors.RESET}\n")
                else:
                    print(f"{agent.Colors.YELLOW}⚠ Failed to send daily summary{agent.Colors.RESET}\n")

            except Exception as e:
                print(f"{agent.Colors.YELLOW}⚠ Email error: {e}{agent.Colors.RESET}\n")
                logging.error(f"Email error: {e}", exc_info=True)

        return True

    except Exception as e:
        logging.error(f"Error generating close summary: {e}", exc_info=True)
        print(f"{agent.Colors.RED}Error: {e}{agent.Colors.RESET}")
        return False
