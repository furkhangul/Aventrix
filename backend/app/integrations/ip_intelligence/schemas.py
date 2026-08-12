from dataclasses import dataclass


@dataclass
class IPIntelligenceResult:
    country: str | None = None
    country_code: str | None = None
    region: str | None = None
    city: str | None = None
    district: str | None = None
    timezone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    isp: str | None = None
    asn: str | None = None
    organization: str | None = None
    hostname: str | None = None
    is_mobile: bool | None = None
    is_vpn: str = "UNKNOWN"
    is_proxy: str = "UNKNOWN"
    is_tor: str = "UNKNOWN"
    is_hosting: str = "UNKNOWN"
    provider: str = "unknown"
