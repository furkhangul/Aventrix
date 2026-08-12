import httpx

from app.core.config import get_settings
from app.integrations.reputation.base import ReputationProvider
from app.integrations.reputation.schemas import ReputationResult

settings = get_settings()


class SafeBrowsingReputationProvider(ReputationProvider):
    """Real provider, shaped for Google Safe Browsing v4's threatMatches:find. Inert until REPUTATION_API_KEY is set."""

    name = "safe_browsing"

    @property
    def is_configured(self) -> bool:
        return bool(settings.reputation_api_key)

    async def check(self, domain: str) -> ReputationResult | None:
        if not self.is_configured:
            return None

        body = {
            "client": {"clientId": settings.app_name, "clientVersion": "1.0.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": f"https://{domain}"}],
            },
        }
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.post(
                    "https://safebrowsing.googleapis.com/v4/threatMatches:find",
                    params={"key": settings.reputation_api_key},
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        matches = data.get("matches") or []
        if matches:
            categories = sorted({m.get("threatType", "UNKNOWN") for m in matches})
            return ReputationResult(verdict="malicious", categories=categories, provider="safe_browsing")
        return ReputationResult(verdict="clean", categories=[], provider="safe_browsing")
