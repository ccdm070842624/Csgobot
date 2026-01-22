"""Notification system for CS:GO Trading Bot"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime


class NotificationSystem:
    """Handle various notification methods"""

    def __init__(self, config):
        """
        Initialize notification system

        Args:
            config: Configuration instance
        """
        self.config = config
        self.enabled = config.get('notifications.enabled', True)

    def send_trade_signal(
        self,
        item: str,
        action: str,
        confidence: float,
        current_price: float,
        predicted_price: Optional[float] = None,
        reasons: Optional[List[str]] = None
    ):
        """
        Send trade signal notification

        Args:
            item: Item name
            action: Trade action (BUY, SELL, HOLD, WAIT)
            confidence: Confidence level (0-100)
            current_price: Current market price
            predicted_price: Predicted future price
            reasons: List of reasons for the recommendation
        """
        if not self.enabled:
            return

        # Console notification
        if self._should_notify_console(action, confidence):
            self._notify_console(item, action, confidence, current_price, predicted_price, reasons)

        # Email notification
        if self._should_notify_email(action, confidence):
            self._notify_email(item, action, confidence, current_price, predicted_price, reasons)

        # Telegram notification (placeholder)
        if self.config.get('notifications.telegram.enabled'):
            self._notify_telegram(item, action, confidence, current_price, predicted_price)

    def _should_notify_console(self, action: str, confidence: float) -> bool:
        """Check if console notification should be sent"""
        if not self.config.get('notifications.console.enabled', True):
            return False

        min_confidence = self.config.get('notifications.console.min_confidence', 60)

        if action == 'BUY' and self.config.get('notifications.console.show_buy_signals', True):
            return confidence >= min_confidence
        elif action == 'SELL' and self.config.get('notifications.console.show_sell_signals', True):
            return confidence >= min_confidence

        return False

    def _should_notify_email(self, action: str, confidence: float) -> bool:
        """Check if email notification should be sent"""
        if not self.config.get('notifications.email.enabled', False):
            return False

        return action in ['BUY', 'SELL'] and confidence >= 70

    def _notify_console(
        self,
        item: str,
        action: str,
        confidence: float,
        current_price: float,
        predicted_price: Optional[float],
        reasons: Optional[List[str]]
    ):
        """Send console notification with ASCII art"""
        emoji_map = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡',
            'WAIT': '⚪'
        }

        print("\n" + "=" * 80)
        print(f"{emoji_map.get(action, '❓')} TRADE ALERT: {action}")
        print("=" * 80)
        print(f"Item:       {item}")
        print(f"Action:     {action}")
        print(f"Confidence: {confidence:.0f}%")
        print(f"Price:      ${current_price:.2f}")

        if predicted_price:
            change = predicted_price - current_price
            change_pct = (change / current_price) * 100
            print(f"Predicted:  ${predicted_price:.2f} ({change_pct:+.1f}%)")

        if reasons:
            print("\nReasons:")
            for reason in reasons:
                print(f"  • {reason}")

        print("=" * 80 + "\n")

    def _notify_email(
        self,
        item: str,
        action: str,
        confidence: float,
        current_price: float,
        predicted_price: Optional[float],
        reasons: Optional[List[str]]
    ):
        """Send email notification"""
        try:
            smtp_server = self.config.get('notifications.email.smtp_server')
            smtp_port = self.config.get('notifications.email.smtp_port')
            sender = self.config.get('notifications.email.sender')
            password = self.config.get('notifications.email.password')
            recipients = self.config.get('notifications.email.recipients', [])

            if not all([smtp_server, sender, password, recipients]):
                return

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"CS:GO Bot Alert: {action} {item}"
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)

            # Create HTML content
            html_content = self._create_email_html(
                item, action, confidence, current_price, predicted_price, reasons
            )

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)

            print(f"📧 Email notification sent to {len(recipients)} recipient(s)")

        except Exception as e:
            print(f"⚠️  Failed to send email notification: {e}")

    def _create_email_html(
        self,
        item: str,
        action: str,
        confidence: float,
        current_price: float,
        predicted_price: Optional[float],
        reasons: Optional[List[str]]
    ) -> str:
        """Create HTML email content"""
        color_map = {
            'BUY': '#28a745',
            'SELL': '#dc3545',
            'HOLD': '#ffc107',
            'WAIT': '#6c757d'
        }

        color = color_map.get(action, '#007bff')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: {color}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .info {{ margin: 10px 0; }}
                .reasons {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{action} Signal</h1>
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div class="content">
                <div class="info"><strong>Item:</strong> {item}</div>
                <div class="info"><strong>Action:</strong> {action}</div>
                <div class="info"><strong>Confidence:</strong> {confidence:.0f}%</div>
                <div class="info"><strong>Current Price:</strong> ${current_price:.2f}</div>
        """

        if predicted_price:
            change = predicted_price - current_price
            change_pct = (change / current_price) * 100
            html += f"""
                <div class="info"><strong>Predicted Price:</strong> ${predicted_price:.2f} ({change_pct:+.1f}%)</div>
            """

        if reasons:
            html += """
                <div class="reasons">
                    <strong>Reasons:</strong>
                    <ul>
            """
            for reason in reasons:
                html += f"<li>{reason}</li>"
            html += """
                    </ul>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _notify_telegram(
        self,
        item: str,
        action: str,
        confidence: float,
        current_price: float,
        predicted_price: Optional[float]
    ):
        """Send Telegram notification (placeholder)"""
        # Placeholder for Telegram integration
        # Would use requests to send message via Telegram Bot API
        pass

    def send_summary(self, total_items: int, buy_signals: int, sell_signals: int):
        """Send analysis summary"""
        if not self.enabled or not self.config.get('notifications.console.enabled', True):
            return

        print("\n" + "=" * 80)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"Total Items Analyzed: {total_items}")
        print(f"Buy Signals:          {buy_signals}")
        print(f"Sell Signals:         {sell_signals}")
        print("=" * 80 + "\n")
