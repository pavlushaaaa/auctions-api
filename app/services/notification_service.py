import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from app.models.notification import Notification, NotificationType, NotificationChannel
from app.core.config import settings
from datetime import datetime


class EmailService:
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 1025)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@auctions.com')

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            if self.smtp_username and self.smtp_password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.from_email, to_email, message.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.sendmail(self.from_email, to_email, message.as_string())

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False


class NotificationService:
    def __init__(self):
        self.email_service = EmailService()

    def create_notification(
        self,
        db,
        user_id: int,
        notification_type: NotificationType,
        channel: NotificationChannel,
        subject: str,
        message: str,
        auction_id: int = None
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            auction_id=auction_id,
            notification_type=notification_type,
            channel=channel,
            subject=subject,
            message=message
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def send_outbid_notification(self, db, user, auction, new_bid_amount):
        subject = f"You've been outbid on {auction.title}"
        message = f"""
        <html>
        <body>
            <h2>You've been outbid!</h2>
            <p>Unfortunately, someone has placed a higher bid on the auction you were winning.</p>
            <p><strong>Auction:</strong> {auction.title}</p>
            <p><strong>New highest bid:</strong> ${new_bid_amount}</p>
            <p><strong>Your next minimum bid:</strong> ${new_bid_amount + auction.bid_step}</p>
            <p>Don't miss out! Place a new bid now.</p>
        </body>
        </html>
        """

        notification = self.create_notification(
            db, user.id, NotificationType.outbid, NotificationChannel.email,
            subject, message, auction.id
        )

        if self.email_service.send_email(user.email, subject, message):
            notification.sent = True
            notification.sent_at = datetime.utcnow()
            db.commit()

        return notification

    def send_won_notification(self, db, user, auction):
        subject = f"Congratulations! You won {auction.title}"
        message = f"""
        <html>
        <body>
            <h2>Congratulations!</h2>
            <p>You have won the auction!</p>
            <p><strong>Auction:</strong> {auction.title}</p>
            <p><strong>Winning bid:</strong> ${auction.current_price}</p>
            <p>Please proceed with payment to complete your purchase.</p>
        </body>
        </html>
        """

        notification = self.create_notification(
            db, user.id, NotificationType.won, NotificationChannel.email,
            subject, message, auction.id
        )

        if self.email_service.send_email(user.email, subject, message):
            notification.sent = True
            notification.sent_at = datetime.utcnow()
            db.commit()

        return notification

    def send_auction_ended_notification(self, db, user, auction):
        subject = f"Auction ended: {auction.title}"
        message = f"""
        <html>
        <body>
            <h2>Auction Ended</h2>
            <p>The auction you participated in has ended.</p>
            <p><strong>Auction:</strong> {auction.title}</p>
            <p><strong>Final price:</strong> ${auction.current_price}</p>
        </body>
        </html>
        """

        notification = self.create_notification(
            db, user.id, NotificationType.auction_ended, NotificationChannel.email,
            subject, message, auction.id
        )

        if self.email_service.send_email(user.email, subject, message):
            notification.sent = True
            notification.sent_at = datetime.utcnow()
            db.commit()

        return notification

    def send_payment_required_notification(self, db, user, auction):
        subject = f"Payment required for {auction.title}"
        message = f"""
        <html>
        <body>
            <h2>Payment Required</h2>
            <p>Please complete your payment for the auction you won.</p>
            <p><strong>Auction:</strong> {auction.title}</p>
            <p><strong>Amount due:</strong> ${auction.current_price}</p>
            <p>Please submit payment within 48 hours.</p>
        </body>
        </html>
        """

        notification = self.create_notification(
            db, user.id, NotificationType.payment_required, NotificationChannel.email,
            subject, message, auction.id
        )

        if self.email_service.send_email(user.email, subject, message):
            notification.sent = True
            notification.sent_at = datetime.utcnow()
            db.commit()

        return notification


notification_service = NotificationService()
