"""
Real DNS record lookups via dnspython. No API key required — DNS is an open
protocol, and the query goes to a public resolver, not to the target domain
itself, so there's no SSRF surface here the way there is for the SSL check
or the header fetch (both of which open a connection to the domain).
"""

import asyncio

import dns.resolver

RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME"]
LOOKUP_TIMEOUT_SECONDS = 5


def _resolve_sync(domain: str) -> dict[str, list[str]]:
    resolver = dns.resolver.Resolver()
    resolver.timeout = LOOKUP_TIMEOUT_SECONDS
    resolver.lifetime = LOOKUP_TIMEOUT_SECONDS

    results: dict[str, list[str]] = {}
    for record_type in RECORD_TYPES:
        try:
            answers = resolver.resolve(domain, record_type)
            results[record_type] = [str(answer).strip('"') for answer in answers]
        except Exception:
            results[record_type] = []
    return results


async def lookup_dns(domain: str) -> dict[str, list[str]]:
    """dnspython's resolver is synchronous — run it off the event loop thread."""
    return await asyncio.to_thread(_resolve_sync, domain)
