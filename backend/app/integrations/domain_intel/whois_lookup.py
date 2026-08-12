"""
Real WHOIS lookups via python-whois. Like DNS, WHOIS is an open protocol —
no API key needed. The underlying library is a blocking socket client, so
every call runs off the event loop thread with a hard timeout; a slow or
unresponsive WHOIS server degrades to "unavailable" rather than hanging the
scan (spec section 40's fallback principle).
"""

import asyncio
from datetime import date, datetime
from typing import Any

import whois

LOOKUP_TIMEOUT_SECONDS = 10


def _first(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return [str(value)]


def _iso(value: Any) -> str | None:
    single = _first(value)
    if isinstance(single, (datetime, date)):
        return single.isoformat()
    return str(single) if single else None


def _lookup_sync(domain: str) -> dict | None:
    try:
        data = whois.whois(domain)
    except Exception:
        return None
    if not data or not data.get("domain_name"):
        return None

    return {
        "registrar": _first(data.get("registrar")),
        "creation_date": _iso(data.get("creation_date")),
        "expiration_date": _iso(data.get("expiration_date")),
        "name_servers": [ns.lower() for ns in _as_str_list(data.get("name_servers"))],
        "status": _as_str_list(data.get("status")),
    }


async def lookup_whois(domain: str) -> dict | None:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_lookup_sync, domain), timeout=LOOKUP_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        return None
