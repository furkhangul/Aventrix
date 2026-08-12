from app.core.config import get_settings
from app.integrations.ip_intelligence.base import IPIntelligenceProvider
from app.integrations.ip_intelligence.ipapi_provider import IpApiProvider
from app.integrations.ip_intelligence.mock_provider import MockIPIntelligenceProvider
from app.integrations.ip_intelligence.real_provider import IpinfoProvider

settings = get_settings()


def get_ip_provider_chain() -> list[IPIntelligenceProvider]:
    """Provider A -> Provider B -> local fallback, per spec section 40."""
    if settings.use_mock_providers or settings.ip_provider == "mock":
        return [MockIPIntelligenceProvider()]
    # Real provider first; mock acts as the local fallback if it's
    # unconfigured, the IP is unresolvable (e.g. private range), or the
    # call fails, so enrichment never just breaks.
    if settings.ip_provider == "ipapi":
        return [IpApiProvider(), MockIPIntelligenceProvider()]
    return [IpinfoProvider(), MockIPIntelligenceProvider()]
