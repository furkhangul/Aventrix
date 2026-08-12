import ipaddress
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}

# Lightweight guard against obviously-internal destinations. This is not the
# full SSRF defense required for server-side fetching (Link Preview /
# Domain Analyzer, a later phase) — the redirect endpoint never fetches the
# target itself, it only issues an HTTP redirect — but there is no reason to
# let a public link point at localhost or the cloud metadata address either.
_BLOCKED_HOSTNAMES = {"localhost", "0.0.0.0"}
_METADATA_IPS = {"169.254.169.254"}


def validate_target_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError("Target URL must use http:// or https://")
    if not parsed.hostname:
        raise ValueError("Target URL must include a host")

    hostname = parsed.hostname.lower()
    if hostname in _BLOCKED_HOSTNAMES or hostname in _METADATA_IPS:
        raise ValueError("Target URL host is not allowed")

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = None
    if ip and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved):
        raise ValueError("Target URL host is not allowed")

    if len(url) > 2048:
        raise ValueError("Target URL is too long")

    return url
