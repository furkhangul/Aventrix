"""
Aggregates every Security Center check into a single flat list of findings
(spec-requested "bulgular" section): each finding has a severity so the UI
and PDF report can render one prioritized list instead of making the user
cross-reference five separate cards.

Findings carry a `code` + `params` rather than a rendered message — the
frontend is fully i18n'd (7 locales), so translation happens client-side via
security.findings.<code> the same way every other label on this page does.
"""

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


def _finding(severity: str, code: str, params: dict | None = None) -> dict:
    return {"severity": severity, "code": code, "params": params or {}}


def build_findings(
    *,
    headers_info: dict,
    ssl_info: dict | None,
    whois_info: dict | None,
    reputation_info: dict | None,
    dns_propagation: dict | None,
    cookie_info: list[dict],
    robots_info: dict,
    subdomains: list[str],
) -> list[dict]:
    findings: list[dict] = []

    if not headers_info.get("reachable"):
        findings.append(_finding("high", "site_unreachable"))
    else:
        present = headers_info.get("headers", {})
        for header, value in present.items():
            if not value:
                findings.append(_finding("medium", "missing_header", {"header": header}))

    if not ssl_info or not ssl_info.get("valid"):
        findings.append(_finding("high", "no_valid_cert"))
    else:
        days = ssl_info.get("days_remaining")
        if days is not None:
            if days < 0:
                findings.append(_finding("high", "cert_expired"))
            elif days < 14:
                findings.append(_finding("high", "cert_expiring_soon", {"days": days}))
            elif days < 30:
                findings.append(_finding("medium", "cert_expiring", {"days": days}))

    if reputation_info and reputation_info.get("verdict") == "malicious":
        findings.append(_finding("high", "reputation_malicious"))
    elif reputation_info and reputation_info.get("verdict") == "suspicious":
        findings.append(_finding("medium", "reputation_suspicious"))

    if whois_info is None:
        findings.append(_finding("info", "whois_unavailable"))

    if dns_propagation and not dns_propagation.get("consistent", True):
        findings.append(_finding("medium", "dns_propagation_inconsistent"))

    for cookie in cookie_info:
        if cookie["issues"]:
            findings.append(
                _finding("low", "cookie_flags", {"name": cookie["name"], "count": len(cookie["issues"])})
            )

    if robots_info.get("robots_found") and not robots_info.get("sitemap_found"):
        findings.append(_finding("info", "no_sitemap"))

    if len(subdomains) > 15:
        findings.append(_finding("info", "many_subdomains", {"count": len(subdomains)}))

    if not findings:
        findings.append(_finding("info", "no_issues_found"))

    findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))
    return findings
