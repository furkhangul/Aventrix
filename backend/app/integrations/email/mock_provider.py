import logging
from dataclasses import dataclass

from app.integrations.email.base import EmailProvider

logger = logging.getLogger("furoftheweak.email.mock")


@dataclass
class SentMessage:
    to: str
    subject: str
    body_text: str
    body_html: str | None = None


class MockEmailProvider(EmailProvider):
    """
    Development provider: 'sends' by logging and keeping an in-process
    record so tests and local development can inspect what would have been
    sent (e.g. read out the verification token) without any real SMTP/API
    integration configured.
    """

    # Class-level so it survives across request-scoped instances within one process.
    _outbox: list[SentMessage] = []

    async def send(self, to: str, subject: str, body_text: str, body_html: str | None = None) -> bool:
        message = SentMessage(to=to, subject=subject, body_text=body_text, body_html=body_html)
        MockEmailProvider._outbox.append(message)
        logger.info("mock_email_sent", extra={"to": to, "subject": subject})
        return True

    @property
    def is_configured(self) -> bool:
        return True

    @classmethod
    def get_outbox(cls) -> list[SentMessage]:
        return cls._outbox

    @classmethod
    def clear_outbox(cls) -> None:
        cls._outbox.clear()
