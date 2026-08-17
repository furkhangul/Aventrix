"""
Passive subdomain discovery via crt.sh (Certificate Transparency log search).

Deliberately passive: this queries a public CT-log aggregator, not the
target domain itself, so — unlike an active DNS brute-force wordlist scan —
it never sends traffic to the target's own infrastructure and can't be
mistaken for a denial-of-service attempt. crt.sh is a fixed, well-known
public service (not user-controlled input), so this does not go through
safe_fetch's SSRF hostname validation the way a check against the target
domain itself would.
"""

import httpx

CRTSH_URL = "https://crt.sh/"
REQUEST_TIMEOUT_SECONDS = 10.0
MAX_SUBDOMAINS = 40


async def enumerate_subdomains(domain: str) -> list[str]:
    """Returns a sorted, deduplicated list of subdomains seen in CT logs. Never raises."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(CRTSH_URL, params={"q": f"%.{domain}", "output": "json"})
            response.raise_for_status()
            entries = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    found: set[str] = set()
    for entry in entries:
        name_value = entry.get("name_value", "") if isinstance(entry, dict) else ""
        for name in name_value.split("\n"):
            name = name.strip().lower().rstrip(".")
            if not name or "*" in name:
                continue
            if name == domain or name.endswith(f".{domain}"):
                found.add(name)

    return sorted(found)[:MAX_SUBDOMAINS]
