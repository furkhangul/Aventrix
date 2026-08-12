import httpx

from app.core.config import get_settings
from app.integrations.ip_intelligence.base import IPIntelligenceProvider
from app.integrations.ip_intelligence.schemas import IPIntelligenceResult

settings = get_settings()


class IpinfoProvider(IPIntelligenceProvider):
    """Real provider, shaped for ipinfo.io's response format. Inert until IP_INTELLIGENCE_API_KEY is set."""

    name = "ipinfo"

    @property
    def is_configured(self) -> bool:
        return bool(settings.ip_intelligence_api_key)

    async def lookup(self, ip_address: str) -> IPIntelligenceResult | None:
        if not self.is_configured:
            return None

        base_url = settings.ip_intelligence_base_url or "https://ipinfo.io"
        url = f"{base_url.rstrip('/')}/{ip_address}/json"

        try:
            async with httpx.AsyncClient(timeout=settings.ip_intelligence_timeout_seconds) as client:
                response = await client.get(url, params={"token": settings.ip_intelligence_api_key})
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        latitude, longitude = None, None
        loc = data.get("loc")
        if loc and "," in loc:
            try:
                lat_str, lon_str = loc.split(",", 1)
                latitude, longitude = float(lat_str), float(lon_str)
            except ValueError:
                pass

        return IPIntelligenceResult(
            country=data.get("country"),
            region=data.get("region"),
            city=data.get("city"),
            timezone=data.get("timezone"),
            latitude=latitude,
            longitude=longitude,
            isp=data.get("org"),
            organization=data.get("org"),
            provider="ipinfo",
        )
