import logging
import sys

from pythonjsonlogger import json as jsonlogger

from app.core.config import get_settings

settings = get_settings()

_SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "cookie", "refresh_token", "access_token"}


class _RedactSensitiveFilter(logging.Filter):
    """Belt-and-suspenders: strip anything that looks like a secret out of structured log extras."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key in list(record.__dict__.keys()):
            if key.lower() in _SENSITIVE_KEYS:
                record.__dict__[key] = "***REDACTED***"
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "service"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(_RedactSensitiveFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if settings.app_debug else logging.INFO)

    # Quiet down noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
