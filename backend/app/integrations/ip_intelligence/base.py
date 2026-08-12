from abc import ABC, abstractmethod

from app.integrations.ip_intelligence.schemas import IPIntelligenceResult


class IPIntelligenceProvider(ABC):
    """Adapter interface: IPService -> ProviderAdapter -> Provider."""

    name: str = "base"

    @abstractmethod
    async def lookup(self, ip_address: str) -> IPIntelligenceResult | None:
        """Returns None on failure/timeout/unconfigured — never raises to the caller."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError
