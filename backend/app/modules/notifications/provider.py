import asyncio
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings


class MockEmailProvider:
    """Stands in for a real SMTP/transactional email provider (none configured yet)."""

    provider_name = "mock"

    async def send(self, *, to_email: str, title: str, body: str) -> None:
        if "[mock-fail]" in body.lower():
            raise RuntimeError("Mock email provider failed to send notification.")


class SmtpEmailProvider:
    provider_name = "smtp"

    async def send(self, *, to_email: str, title: str, body: str) -> None:
        await asyncio.to_thread(self._send_sync, to_email, title, body)

    def _send_sync(self, to_email: str, title: str, body: str) -> None:
        message = MIMEText(body)
        message["Subject"] = title
        message["From"] = settings.smtp_from_address or settings.smtp_username
        message["To"] = to_email

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
            if settings.smtp_use_tls:
                client.starttls()
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password)
            client.sendmail(message["From"], [to_email], message.as_string())


def get_email_provider():
    provider = settings.email_provider.lower()
    if provider == "mock":
        return MockEmailProvider()
    if provider == "smtp":
        return SmtpEmailProvider()
    raise RuntimeError(f"Unsupported email provider: {settings.email_provider}")
