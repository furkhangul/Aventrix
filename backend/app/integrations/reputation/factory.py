from app.core.config import get_settings
from app.integrations.reputation.base import ReputationProvider
from app.integrations.reputation.mock_provider import MockReputationProvider
from app.integrations.reputation.real_provider import SafeBrowsingReputationProvider

settings = get_settings()


def get_reputation_provider_chain() -> list[ReputationProvider]:
    """Provider A -> local fallback, per spec section 40."""
    if settings.use_mock_providers or settings.reputation_provider == "mock":
        return [MockReputationProvider()]
    return [SafeBrowsingReputationProvider(), MockReputationProvider()]
