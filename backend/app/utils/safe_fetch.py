"""
Hardened SSRF-safe HTTP fetcher.

app/utils/url_validation.py's validate_target_url() is a cheap, string-only
pre-check used at link-creation time — it never issues a request itself, it
only decides whether a redirect *may later* point somewhere. It is not
enough for code that actually makes an outbound request on the server's
behalf (URL Tools' analyzer/redirect-checker, Security Center's SSL/header
checks): a hostname can resolve to a private IP that's only visible after
DNS resolution, and a redirect response can point anywhere, bypassing a
check that only ran once up front.

safe_fetch() closes both of those gaps: it resolves each hostname itself and
validates the resolved IP before connecting, and re-validates on *every* hop
of a redirect chain rather than trusting httpx's built-in redirect
following. It does not pin the TLS connection to the resolved IP, so a
narrow DNS-rebinding window between our lookup and httpx's own connect
remains — see docs/SECURITY.md for that documented residual risk.
"""

import asyncio
import ipaddress
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx

ALLOWED_SCHEMES = {"http", "https"}
DEFAULT_TIMEOUT_SECONDS = 8.0
MAX_REDIRECTS = 10
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB
MAX_URL_LENGTH = 2048

_BLOCKED_HOSTNAMES = {"localhost", "0.0.0.0"}
_METADATA_IPS = {"169.254.169.254"}


class UnsafeUrlError(ValueError):
    """Raised when a URL (or a redirect hop) resolves to a disallowed destination."""


@dataclass
class Hop:
    url: str
    status_code: int
    location: str | None = None
    elapsed_ms: float = 0.0


@dataclass
class FetchResult:
    final_url: str
    status_code: int
    headers: httpx.Headers
    body: bytes
    hops: list[Hop] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _validate_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address, hostname: str) -> None:
    if str(ip) in _METADATA_IPS:
        raise UnsafeUrlError("Host resolves to a cloud metadata address")
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        raise UnsafeUrlError(f"Host '{hostname}' resolves to a non-public address")


async def _resolve_and_validate_host(hostname: str) -> None:
    hostname_lower = hostname.lower()
    if hostname_lower in _BLOCKED_HOSTNAMES:
        raise UnsafeUrlError(f"Host '{hostname}' is not allowed")

    try:
        _validate_ip(ipaddress.ip_address(hostname_lower), hostname)
        return
    except ValueError:
        pass  # Not a literal IP — resolve it below.

    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(hostname_lower, None)
    except OSError as exc:
        raise UnsafeUrlError(f"Could not resolve host '{hostname}'") from exc

    if not infos:
        raise UnsafeUrlError(f"Could not resolve host '{hostname}'")

    for family, _type, _proto, _canonname, sockaddr in infos:
        _validate_ip(ipaddress.ip_address(sockaddr[0]), hostname)


async def validate_hostname_for_connect(hostname: str) -> None:
    """
    Public entry point for code that connects to a bare hostname without
    going through httpx (e.g. a raw TLS socket for a certificate check, or a
    WHOIS/DNS lookup). Raises UnsafeUrlError for the same reasons
    validate_url_for_fetch would.
    """
    await _resolve_and_validate_host(hostname)


async def validate_url_for_fetch(url: str) -> str:
    """Validates scheme/host/length and that the host resolves publicly. Raises UnsafeUrlError."""
    url = url.strip()
    if len(url) > MAX_URL_LENGTH:
        raise UnsafeUrlError("URL is too long")

    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeUrlError("URL must use http:// or https://")
    if not parsed.hostname:
        raise UnsafeUrlError("URL must include a host")

    await _resolve_and_validate_host(parsed.hostname)
    return url


async def safe_fetch(
    url: str,
    *,
    method: str = "GET",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_redirects: int = MAX_REDIRECTS,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> FetchResult:
    """
    Fetches a URL with redirects followed manually so every hop — including
    ones an attacker controls via an open redirect on an otherwise-safe host
    — is independently validated before being connected to. Never follows
    more than max_redirects hops and never reads more than max_bytes of body.
    """
    current_url = url
    hops: list[Hop] = []
    started = time.monotonic()

    async with httpx.AsyncClient(follow_redirects=False, timeout=timeout_seconds) as client:
        for _ in range(max_redirects + 1):
            current_url = await validate_url_for_fetch(current_url)
            try:
                async with client.stream(method, current_url) as response:
                    hop_started = time.monotonic()
                    body = b""
                    async for chunk in response.aiter_bytes():
                        body += chunk
                        if len(body) > max_bytes:
                            break
                    hop_elapsed_ms = (time.monotonic() - hop_started) * 1000
                    location = response.headers.get("location")
                    hops.append(
                        Hop(
                            url=current_url,
                            status_code=response.status_code,
                            location=location,
                            elapsed_ms=round(hop_elapsed_ms, 1),
                        )
                    )

                    if response.is_redirect and location:
                        current_url = urljoin(current_url, location)
                        continue

                    return FetchResult(
                        final_url=current_url,
                        status_code=response.status_code,
                        headers=response.headers,
                        body=body[:max_bytes],
                        hops=hops,
                        elapsed_ms=round((time.monotonic() - started) * 1000, 1),
                    )
            except httpx.HTTPError as exc:
                raise UnsafeUrlError(f"Request failed: {exc}") from exc

    raise UnsafeUrlError("Too many redirects")
