from abc import ABC, abstractmethod

from app.integrations.reputation.schemas import ReputationResult


class ReputationProvider(ABC):
    """Adapter interface: SecurityCenterService -> ProviderAdapter -> Provider."""

    name: str = "base"

    @abstractmethod
    async def check(self, domain: str) -> ReputationResult | None:
        """Returns None on failure/timeout/unconfigured — never raises to the caller."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError
