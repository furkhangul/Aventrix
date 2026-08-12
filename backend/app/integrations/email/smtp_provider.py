import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings
from app.integrations.email.base import EmailProvider

logger = logging.getLogger("furoftheweak.email.smtp")
settings = get_settings()


class SmtpEmailProvider(EmailProvider):
    """Real provider. Inert (send() is a no-op returning False) until SMTP_* is configured."""

    @property
    def is_configured(self) -> bool:
        return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)

    async def send(self, to: str, subject: str, body_text: str, body_html: str | None = None) -> bool:
        if not self.is_configured:
            logger.warning("smtp_not_configured", extra={"to": to})
            return False
        return await asyncio.to_thread(self._send_sync, to, subject, body_text, body_html)

    def _send_sync(self, to: str, subject: str, body_text: str, body_html: str | None) -> bool:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.email_from_address
        message["To"] = to
        message.attach(MIMEText(body_text, "plain"))
        if body_html:
            message.attach(MIMEText(body_html, "html"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.email_from_address, [to], message.as_string())
            return True
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("smtp_send_failed", extra={"to": to, "error": str(exc)})
            return False
