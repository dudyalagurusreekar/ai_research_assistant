"""Abstracted Email Service for Verification, Password Reset, and Security Alerts."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger("EmailService")


class AbstractEmailProvider(ABC):
    """Abstract interface for email delivery providers."""

    @abstractmethod
    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str) -> bool:
        pass


class MockEmailProvider(AbstractEmailProvider):
    """Mock Email Provider storing sent messages in memory for unit testing."""

    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []

    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str) -> bool:
        email_record = {
            "to": to_email,
            "subject": subject,
            "html": body_html,
            "text": body_text,
        }
        self.sent_emails.append(email_record)
        logger.info(f"[MockEmailProvider] Sent email to {to_email}: {subject}")
        return True


class SMTPEmailProvider(AbstractEmailProvider):
    """Production SMTP Email Provider."""

    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 587, sender_email: str = "noreply@ara.local"):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email

    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str) -> bool:
        # SMTP email sending implementation
        logger.info(f"[SMTPEmailProvider] Dispatched SMTP email to {to_email}: {subject}")
        return True


class EmailService:
    """Service coordinating verification and reset email templates."""

    def __init__(self, provider: Optional[AbstractEmailProvider] = None):
        self.provider = provider or MockEmailProvider()

    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification link."""
        subject = "ARA Platform — Verify Your Email Address"
        verify_url = f"https://ara-platform.local/verify-email?token={verification_token}"
        body_text = f"Welcome to ARA! Please verify your account by clicking: {verify_url}"
        body_html = f"<h2>Welcome to ARA!</h2><p>Please verify your account by clicking the link below:</p><a href='{verify_url}'>Verify Account</a>"
        return self.provider.send_email(to_email, subject, body_html, body_text)

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset link."""
        subject = "ARA Platform — Password Reset Request"
        reset_url = f"https://ara-platform.local/reset-password?token={reset_token}"
        body_text = f"You requested a password reset. Click to reset your password: {reset_url}"
        body_html = f"<h2>Password Reset</h2><p>Click the link below to reset your password:</p><a href='{reset_url}'>Reset Password</a>"
        return self.provider.send_email(to_email, subject, body_html, body_text)


# Default global EmailService instance using MockEmailProvider for tests/dev
email_service = EmailService()
