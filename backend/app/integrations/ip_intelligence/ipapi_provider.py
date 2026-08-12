import httpx

from app.core.config import get_settings
from app.integrations.ip_intelligence.base import IPIntelligenceProvider
from app.integrations.ip_intelligence.schemas import IPIntelligenceResult

settings = get_settings()

_FIELDS = (
    "status,message,country,countryCode,regionName,city,district,timezone,lat,lon,"
    "isp,org,as,reverse,mobile,proxy,hosting,query"
)


class IpApiProvider(IPIntelligenceProvider):
    """
    Real provider backed by ip-api.com's free JSON endpoint — no API key
    required, so unlike IpinfoProvider it's always "configured". Private/
    reserved-range IPs (e.g. local dev traffic) come back as a non-success
    status, in which case lookup() returns None and the mock provider
    fills in for local testing, same as any other provider failure.
    """

    name = "ipapi"

    @property
    def is_configured(self) -> bool:
        return True

    async def lookup(self, ip_address: str) -> IPIntelligenceResult | None:
        base_url = settings.ip_intelligence_base_url or "http://ip-api.com"
        url = f"{base_url.rstrip('/')}/json/{ip_address}"

        try:
            async with httpx.AsyncClient(timeout=settings.ip_intelligence_timeout_seconds) as client:
                response = await client.get(url, params={"fields": _FIELDS})
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        if data.get("status") != "success":
            return None

        asn = None
        as_field = data.get("as")
        if as_field:
            asn = as_field.split(" ", 1)[0] or None

        # ip-api's "proxy" flag covers proxy/VPN/Tor exit nodes without
        # distinguishing which — reported as is_proxy, leaving is_vpn/is_tor
        # UNKNOWN rather than guessing a specific one of the three.
        return IPIntelligenceResult(
            country=data.get("country"),
            country_code=data.get("countryCode"),
            region=data.get("regionName"),
            city=data.get("city"),
            district=data.get("district") or None,
            timezone=data.get("timezone"),
            latitude=data.get("lat"),
            longitude=data.get("lon"),
            isp=data.get("isp"),
            asn=asn,
            organization=data.get("org") or data.get("isp"),
            hostname=data.get("reverse") or None,
            is_mobile=bool(data.get("mobile")) if "mobile" in data else None,
            is_proxy="YES" if data.get("proxy") else "NO",
            is_hosting="YES" if data.get("hosting") else "NO",
            provider="ipapi",
        )
