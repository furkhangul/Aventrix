from functools import lru_cache

from app.core.config import get_settings
from app.integrations.email.base import EmailProvider
from app.integrations.email.mock_provider import MockEmailProvider
from app.integrations.email.smtp_provider import SmtpEmailProvider

settings = get_settings()


@lru_cache
def get_email_provider() -> EmailProvider:
    if settings.use_mock_providers or settings.email_provider == "mock":
        return MockEmailProvider()
    if settings.email_provider == "smtp":
        return SmtpEmailProvider()
    # Unknown/unset provider: never crash the app, just report unavailable.
    return SmtpEmailProvider()
