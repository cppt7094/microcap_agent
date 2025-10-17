"""
Email Alert System for Portfolio Monitoring Agent
Sends email notifications for critical alerts and daily summaries
"""

import sys
import codecs
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
from config import Config

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class EmailAlertSystem:
    """Handles email notifications for portfolio alerts"""

    def __init__(self):
        """Initialize email system with config"""
        self.sender_email = Config.EMAIL_ADDRESS
        self.app_password = Config.EMAIL_APP_PASSWORD
        self.recipient_email = Config.EMAIL_ADDRESS  # Send to yourself

    def send_alert_email(self, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        """
        Send an email alert

        Args:
            subject: Email subject line
            body_text: Plain text body
            body_html: Optional HTML body

        Returns:
            Boolean success status
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            # Attach plain text
            msg.attach(MIMEText(body_text, 'plain'))

            # Attach HTML if provided
            if body_html:
                msg.attach(MIMEText(body_html, 'html'))

            # Send via Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.app_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())

            logging.info(f"Email sent successfully: {subject}")
            return True

        except Exception as e:
            logging.error(f"Failed to send email: {e}", exc_info=True)
            return False

    def send_critical_alerts(self, analysis_data: List[Dict], portfolio_value: float) -> bool:
        """
        Send email for critical alerts (gains/losses above thresholds)

        Args:
            analysis_data: Position analysis results
            portfolio_value: Current portfolio value

        Returns:
            Boolean success status
        """
        # Filter for critical alerts
        critical_alerts = [
            pos for pos in analysis_data
            if pos['action_required'] and pos['alert_level'] in ['strong', 'critical', 'stop_loss']
        ]

        if not critical_alerts:
            return False

        # Build email subject
        alert_count = len(critical_alerts)
        subject = f"🚨 {alert_count} Critical Alert{'s' if alert_count > 1 else ''} - Project Oriana"

        # Build plain text body
        body_text = f"""Project Oriana - Portfolio Alert
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Portfolio Value: ${portfolio_value:,.2f}

CRITICAL ALERTS:
"""

        for pos in critical_alerts:
            symbol = pos['symbol']
            message = pos['alert_message']
            pct = pos['pct_change'] * 100
            price = pos['current_price']

            body_text += f"\n{symbol}: {message}"
            body_text += f"\n  Current Price: ${price:.2f} ({pct:+.1f}%)"
            body_text += f"\n  Action Required: YES\n"

        body_text += "\n---\nCheck your monitoring dashboard for full details."

        # Build HTML body
        body_html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: #ff4444; color: white; padding: 15px; }}
        .alert {{ border-left: 4px solid #ff4444; padding: 10px; margin: 10px 0; background-color: #fff3f3; }}
        .symbol {{ font-weight: bold; font-size: 18px; }}
        .details {{ color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🚨 Project Oriana - Critical Alert</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <p><strong>Portfolio Value:</strong> ${portfolio_value:,.2f}</p>

    <h3>Critical Alerts ({alert_count}):</h3>
"""

        for pos in critical_alerts:
            symbol = pos['symbol']
            message = pos['alert_message']
            pct = pos['pct_change'] * 100
            price = pos['current_price']

            body_html += f"""
    <div class="alert">
        <div class="symbol">{symbol}</div>
        <div>{message}</div>
        <div class="details">
            Current Price: ${price:.2f} ({pct:+.1f}%)
        </div>
    </div>
"""

        body_html += """
    <hr>
    <p><em>Check your monitoring dashboard for full details.</em></p>
</body>
</html>
"""

        return self.send_alert_email(subject, body_text, body_html)

    def send_daily_summary(self, summary: Dict) -> bool:
        """
        Send daily market close summary via email

        Args:
            summary: Market close summary data

        Returns:
            Boolean success status
        """
        try:
            perf = summary['daily_performance']
            rebal = summary['rebalancing_status']

            # Build subject
            change_pct = perf['total_change_pct']
            emoji = "📈" if change_pct > 0 else "📉"
            subject = f"{emoji} Daily Summary: {change_pct:+.1f}% - Project Oriana"

            # Build plain text body
            body_text = f"""Project Oriana - Market Close Summary
Generated: {summary['timestamp']}

DAILY PERFORMANCE:
Portfolio Value: ${perf['close_value']:,.2f}
Daily Change: ${perf['total_change']:+,.2f} ({perf['total_change_pct']:+.1f}%)

Best Performer: {perf['best_performer']['symbol']} ({perf['best_performer']['pct_change']:+.1f}%)
Worst Performer: {perf['worst_performer']['symbol']} ({perf['worst_performer']['pct_change']:+.1f}%)

Green Positions: {perf['green_positions']}
Red Positions: {perf['red_positions']}

REBALANCING STATUS:
Completion: {rebal['completion_pct']:.1f}%
Capital Needed: ${rebal['capital_needed']:.2f}
Cash Available: ${rebal['cash_available']:.2f}
Positions at Target: {rebal['positions_at_target']}
Positions Pending: {rebal['positions_pending']}

TOMORROW'S WATCHLIST:
"""

            for item in summary['tomorrows_watchlist']:
                symbol = item['symbol']
                if 'current_pct' in item:
                    body_text += f"  {symbol}: {item['current_pct']:.1f}% (approaching {item['threshold_name']})\n"
                else:
                    body_text += f"  {symbol}: {item['notes']}\n"

            if summary['alerts_triggered']:
                body_text += f"\nALERTS TODAY: {len(summary['alerts_triggered'])}\n"
                for alert in summary['alerts_triggered']:
                    body_text += f"  - {alert}\n"

            # Build HTML body
            change_color = "#00aa00" if change_pct > 0 else "#aa0000"

            body_html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: #4CAF50; color: white; padding: 15px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ padding: 5px 0; }}
        .positive {{ color: #00aa00; }}
        .negative {{ color: #aa0000; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{emoji} Project Oriana - Market Close Summary</h2>
        <p>{summary['timestamp']}</p>
    </div>

    <div class="section">
        <h3>Daily Performance</h3>
        <div class="metric"><strong>Portfolio Value:</strong> ${perf['close_value']:,.2f}</div>
        <div class="metric" style="color: {change_color};">
            <strong>Daily Change:</strong> ${perf['total_change']:+,.2f} ({perf['total_change_pct']:+.1f}%)
        </div>
        <div class="metric">
            <strong>Best:</strong> {perf['best_performer']['symbol']} ({perf['best_performer']['pct_change']:+.1f}%)
        </div>
        <div class="metric">
            <strong>Worst:</strong> {perf['worst_performer']['symbol']} ({perf['worst_performer']['pct_change']:+.1f}%)
        </div>
    </div>

    <div class="section">
        <h3>Rebalancing Status</h3>
        <div class="metric"><strong>Completion:</strong> {rebal['completion_pct']:.1f}%</div>
        <div class="metric"><strong>Cash Available:</strong> ${rebal['cash_available']:.2f}</div>
        <div class="metric"><strong>Capital Needed:</strong> ${rebal['capital_needed']:.2f}</div>
    </div>

    <div class="section">
        <h3>Tomorrow's Watchlist</h3>
        <ul>
"""

            for item in summary['tomorrows_watchlist']:
                symbol = item['symbol']
                if 'current_pct' in item:
                    body_html += f"<li><strong>{symbol}</strong>: {item['current_pct']:.1f}% (approaching {item['threshold_name']})</li>"
                else:
                    body_html += f"<li><strong>{symbol}</strong>: {item['notes']}</li>"

            body_html += """
        </ul>
    </div>
</body>
</html>
"""

            return self.send_alert_email(subject, body_text, body_html)

        except Exception as e:
            logging.error(f"Error sending daily summary email: {e}", exc_info=True)
            return False


def test_email():
    """Test email functionality"""
    print("\n" + "="*70)
    print("  EMAIL ALERT SYSTEM TEST")
    print("="*70 + "\n")

    # Validate config
    try:
        Config.validate(require_email=True)
        print("✓ Email configuration validated\n")
    except ValueError as e:
        print(f"❌ Email configuration error: {e}")
        return False

    # Create email system
    email_system = EmailAlertSystem()

    # Send test email
    print("Sending test email...")

    subject = "🧪 Test Email - Project Oriana"
    body_text = f"""This is a test email from your Project Oriana monitoring agent.

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this, email alerts are configured correctly!
"""

    body_html = f"""
<html>
<body>
    <h2>🧪 Test Email - Project Oriana</h2>
    <p>This is a test email from your monitoring agent.</p>
    <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>If you received this, email alerts are configured correctly!</p>
</body>
</html>
"""

    success = email_system.send_alert_email(subject, body_text, body_html)

    if success:
        print(f"✓ Test email sent successfully to {Config.EMAIL_ADDRESS}")
        print("\nCheck your inbox!")
        print("="*70)
        return True
    else:
        print("❌ Failed to send test email")
        print("="*70)
        return False


if __name__ == "__main__":
    import sys
    success = test_email()
    sys.exit(0 if success else 1)
