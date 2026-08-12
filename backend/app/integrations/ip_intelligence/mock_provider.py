import hashlib

from app.integrations.ip_intelligence.base import IPIntelligenceProvider
from app.integrations.ip_intelligence.schemas import IPIntelligenceResult

# Small set of plausible, clearly-fictional-enough sample locations used so
# local development and tests have realistic-looking (but not real) data
# without calling any external service.
_SAMPLE_LOCATIONS = [
    {
        "country": "Turkey", "country_code": "TR", "region": "Istanbul", "city": "Istanbul", "district": "Maltepe",
        "timezone": "Europe/Istanbul", "latitude": 40.9354, "longitude": 29.1526,
        "isp": "Turk Telekom", "asn": "AS9121", "organization": "Turk Telekom",
        "hostname": "host-static.maltepe.ttnet.net.tr",
    },
    {
        "country": "Germany", "country_code": "DE", "region": "Berlin", "city": "Berlin", "district": "Mitte",
        "timezone": "Europe/Berlin", "latitude": 52.52, "longitude": 13.405,
        "isp": "Deutsche Telekom", "asn": "AS3320", "organization": "Deutsche Telekom AG",
        "hostname": "p-mitte.dip0.t-ipconnect.de",
    },
    {
        "country": "United States", "country_code": "US", "region": "California", "city": "San Francisco",
        "district": "Mission District", "timezone": "America/Los_Angeles", "latitude": 37.7749,
        "longitude": -122.4194, "isp": "Comcast Cable", "asn": "AS7922",
        "organization": "Comcast Cable Communications", "hostname": "c-mission.hsd1.ca.comcast.net",
    },
    {
        "country": "United Kingdom", "country_code": "GB", "region": "England", "city": "London",
        "district": "Camden", "timezone": "Europe/London", "latitude": 51.5074, "longitude": -0.1278,
        "isp": "BT Group", "asn": "AS2856", "organization": "British Telecommunications",
        "hostname": "camden.host.btopenworld.com",
    },
    {
        "country": "Netherlands", "country_code": "NL", "region": "North Holland", "city": "Amsterdam",
        "district": "De Pijp", "timezone": "Europe/Amsterdam", "latitude": 52.3676, "longitude": 4.9041,
        "isp": "KPN", "asn": "AS1136", "organization": "KPN B.V.", "hostname": "depijp.kpn.customer.net",
    },
    {
        "country": "Japan", "country_code": "JP", "region": "Tokyo", "city": "Tokyo", "district": "Shibuya",
        "timezone": "Asia/Tokyo", "latitude": 35.6762, "longitude": 139.6503,
        "isp": "NTT Communications", "asn": "AS4713", "organization": "NTT Communications Corp",
        "hostname": "shibuya.flets-east.jp",
    },
]


class MockIPIntelligenceProvider(IPIntelligenceProvider):
    name = "mock"

    @property
    def is_configured(self) -> bool:
        return True

    async def lookup(self, ip_address: str) -> IPIntelligenceResult:
        # Deterministic per-IP so repeated visits from the "same" address
        # look consistent in the dashboard during local development.
        digest = hashlib.sha256(ip_address.encode()).digest()
        location = _SAMPLE_LOCATIONS[digest[0] % len(_SAMPLE_LOCATIONS)]

        return IPIntelligenceResult(
            **location,
            is_vpn="YES" if digest[1] % 10 == 0 else "NO",
            is_proxy="NO",
            is_tor="NO",
            is_hosting="YES" if digest[2] % 8 == 0 else "NO",
            is_mobile=digest[3] % 4 == 0,
            provider="mock",
        )
