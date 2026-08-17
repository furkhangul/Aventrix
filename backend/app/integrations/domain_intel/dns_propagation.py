"""
DNS propagation checker: resolves the domain's A record against several
well-known public resolvers directly (bypassing the local/OS resolver
cache) and reports whether they agree. Same open-protocol reasoning as
dns_lookup.py — no SSRF surface, since dnspython talks to the resolver IP,
never to the target domain itself.
"""

import asyncio

import dns.resolver

LOOKUP_TIMEOUT_SECONDS = 5

PUBLIC_RESOLVERS = {
    "google": "8.8.8.8",
    "cloudflare": "1.1.1.1",
    "quad9": "9.9.9.9",
    "opendns": "208.67.222.222",
}


def _resolve_one(domain: str, resolver_ip: str) -> list[str]:
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [resolver_ip]
    resolver.timeout = LOOKUP_TIMEOUT_SECONDS
    resolver.lifetime = LOOKUP_TIMEOUT_SECONDS
    try:
        answers = resolver.resolve(domain, "A")
        return sorted(str(answer) for answer in answers)
    except Exception:
        return []


def _check_sync(domain: str) -> dict[str, list[str]]:
    return {name: _resolve_one(domain, ip) for name, ip in PUBLIC_RESOLVERS.items()}


async def check_dns_propagation(domain: str) -> dict:
    """
    Returns {"resolvers": {name: [ips]}, "consistent": bool} — consistent is
    True when every resolver that returned a non-empty answer agrees.
    """
    resolvers = await asyncio.to_thread(_check_sync, domain)
    answered = [set(ips) for ips in resolvers.values() if ips]
    consistent = len(set(frozenset(s) for s in answered)) <= 1

    return {"resolvers": resolvers, "consistent": consistent}
