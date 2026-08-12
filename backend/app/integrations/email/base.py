from abc import ABC, abstractmethod


class EmailProvider(ABC):
    """Adapter interface — swap providers without touching call sites."""

    @abstractmethod
    async def send(self, to: str, subject: str, body_text: str, body_html: str | None = None) -> bool:
        """Returns True if the message was accepted for delivery."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError
