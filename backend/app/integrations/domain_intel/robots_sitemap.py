"""
robots.txt / sitemap.xml analyzer. Both requests go through safe_fetch, so
they get the same SSRF hostname/redirect validation as the security-header
check — this connects to the target domain itself.
"""

import re
from xml.etree import ElementTree

from app.utils.safe_fetch import UnsafeUrlError, safe_fetch

MAX_DISALLOW_RULES = 20
MAX_SITEMAP_URLS = 20


def _parse_robots(text: str) -> dict:
    disallow_rules: list[str] = []
    sitemap_urls: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"(?i)^disallow:\s*(.*)$", line)
        if match and match.group(1) and len(disallow_rules) < MAX_DISALLOW_RULES:
            disallow_rules.append(match.group(1).strip())
            continue
        match = re.match(r"(?i)^sitemap:\s*(.*)$", line)
        if match and match.group(1):
            sitemap_urls.append(match.group(1).strip())
    return {"disallow_rules": disallow_rules, "sitemap_urls": sitemap_urls}


def _count_sitemap_urls(xml_text: str) -> int:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return 0
    # Namespace-agnostic: matches <loc> under either <urlset> or <sitemapindex>.
    return sum(1 for el in root.iter() if el.tag.endswith("}loc") or el.tag == "loc")


async def analyze_robots_and_sitemap(domain: str) -> dict:
    """Never raises — every failure mode degrades to a 'not found' result."""
    result: dict = {
        "robots_found": False,
        "disallow_rules": [],
        "sitemap_found": False,
        "sitemap_url": None,
        "sitemap_url_count": None,
    }

    try:
        robots = await safe_fetch(f"https://{domain}/robots.txt")
    except UnsafeUrlError:
        return result

    sitemap_url_from_robots = None
    if robots.status_code == 200:
        parsed = _parse_robots(robots.body.decode("utf-8", errors="replace"))
        result["robots_found"] = True
        result["disallow_rules"] = parsed["disallow_rules"]
        if parsed["sitemap_urls"]:
            sitemap_url_from_robots = parsed["sitemap_urls"][0]

    sitemap_url = sitemap_url_from_robots or f"https://{domain}/sitemap.xml"
    try:
        sitemap = await safe_fetch(sitemap_url)
    except UnsafeUrlError:
        return result

    if sitemap.status_code == 200:
        result["sitemap_found"] = True
        result["sitemap_url"] = sitemap_url
        result["sitemap_url_count"] = _count_sitemap_urls(sitemap.body.decode("utf-8", errors="replace"))

    return result
