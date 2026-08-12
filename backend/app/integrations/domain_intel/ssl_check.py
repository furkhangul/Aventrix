"""
Real SSL/TLS certificate inspection via a direct socket connection — no API
key needed, but unlike DNS/WHOIS this *does* open a connection to the target
domain, so it goes through the same SSRF hostname/IP validation as any other
outbound fetch before connecting.
"""

import asyncio
import socket
import ssl
from datetime import datetime, timezone

from app.utils.safe_fetch import UnsafeUrlError, validate_hostname_for_connect

CONNECT_TIMEOUT_SECONDS = 6.0


def _fetch_cert_sync(domain: str, port: int, timeout: float) -> dict:
    context = ssl.create_default_context()
    with socket.create_connection((domain, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            cipher = ssock.cipher()
            protocol = ssock.version()
    return {"cert": cert, "cipher": cipher, "protocol": protocol}


async def check_ssl(domain: str, *, port: int = 443, timeout: float = CONNECT_TIMEOUT_SECONDS) -> dict | None:
    try:
        await validate_hostname_for_connect(domain)
    except UnsafeUrlError:
        return None

    try:
        raw = await asyncio.wait_for(
            asyncio.to_thread(_fetch_cert_sync, domain, port, timeout), timeout=timeout + 2
        )
    except Exception:
        return {"valid": False}

    cert = raw["cert"]
    not_after = cert.get("notAfter")
    expires_at = None
    days_remaining = None
    if not_after:
        try:
            expires_dt = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            expires_at = expires_dt.isoformat()
            days_remaining = (expires_dt - datetime.now(timezone.utc)).days
        except ValueError:
            pass

    issuer = dict(pair[0] for pair in cert.get("issuer", []))
    subject = dict(pair[0] for pair in cert.get("subject", []))

    return {
        "valid": True,
        "issuer": issuer.get("organizationName") or issuer.get("commonName"),
        "subject": subject.get("commonName"),
        "expires_at": expires_at,
        "days_remaining": days_remaining,
        "protocol": raw["protocol"],
        "cipher": raw["cipher"][0] if raw["cipher"] else None,
    }
