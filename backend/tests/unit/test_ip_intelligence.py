
from app.integrations.ip_intelligence.mock_provider import MockIPIntelligenceProvider
from app.integrations.ip_intelligence.real_provider import IpinfoProvider


async def test_mock_provider_is_deterministic_per_ip():
    provider = MockIPIntelligenceProvider()
    result1 = await provider.lookup("203.0.113.1")
    result2 = await provider.lookup("203.0.113.1")
    assert result1.country == result2.country
    assert result1.city == result2.city
    assert result1.provider == "mock"


async def test_mock_provider_varies_across_ips():
    provider = MockIPIntelligenceProvider()
    countries = {(await provider.lookup(f"203.0.113.{i}")).country for i in range(1, 30)}
    assert len(countries) > 1


def test_mock_provider_always_configured():
    assert MockIPIntelligenceProvider().is_configured is True


def test_real_provider_unconfigured_without_api_key():
    provider = IpinfoProvider()
    assert provider.is_configured is False


async def test_real_provider_returns_none_when_unconfigured():
    provider = IpinfoProvider()
    result = await provider.lookup("203.0.113.1")
    assert result is None
