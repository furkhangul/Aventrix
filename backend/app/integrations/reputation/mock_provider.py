import hashlib

from app.integrations.reputation.base import ReputationProvider
from app.integrations.reputation.schemas import ReputationResult


class MockReputationProvider(ReputationProvider):
    name = "mock"

    @property
    def is_configured(self) -> bool:
        return True

    async def check(self, domain: str) -> ReputationResult:
        # Deterministic per-domain so repeated scans look consistent in
        # local development, mostly "clean" with an occasional flagged one.
        digest = hashlib.sha256(domain.encode()).digest()
        if digest[0] % 20 == 0:
            return ReputationResult(verdict="suspicious", categories=["low-reputation-mock"], provider="mock")
        return ReputationResult(verdict="clean", categories=[], provider="mock")
