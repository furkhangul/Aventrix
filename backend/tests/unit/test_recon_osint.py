from app.integrations.domain_intel.cookie_analysis import analyze_cookies
from app.integrations.domain_intel.tech_detect import detect_technologies
from app.services.security_findings import build_findings


def test_analyze_cookies_flags_missing_attributes():
    [cookie] = analyze_cookies(["session=abc123; Path=/"])
    assert cookie["name"] == "session"
    assert cookie["secure"] is False
    assert cookie["http_only"] is False
    assert "missing_secure" in cookie["issues"]
    assert "missing_httponly" in cookie["issues"]
    assert "missing_samesite" in cookie["issues"]


def test_analyze_cookies_accepts_fully_flagged_cookie():
    [cookie] = analyze_cookies(["session=abc123; Path=/; Secure; HttpOnly; SameSite=Strict"])
    assert cookie["issues"] == []
    assert cookie["same_site"] == "Strict"


def test_detect_technologies_from_header_and_cookie():
    headers = {"server": "nginx/1.25.0", "cf-ray": "abc123-DFW"}
    found = detect_technologies(headers, ["phpsessid"], body_sample="")
    technologies = {f["technology"] for f in found}
    assert "Nginx" in technologies
    assert "Cloudflare" in technologies
    assert "PHP" in technologies


def test_detect_technologies_from_body_signature():
    found = detect_technologies({}, [], body_sample='<meta name="generator" content="WordPress 6.4" />')
    assert any(f["technology"] == "WordPress" for f in found)


def test_build_findings_flags_missing_headers_and_expiring_cert():
    findings = build_findings(
        headers_info={"reachable": True, "headers": {"content-security-policy": None, "x-frame-options": "DENY"}},
        ssl_info={"valid": True, "days_remaining": 5},
        whois_info=None,
        reputation_info={"verdict": "malicious"},
        dns_propagation={"consistent": False},
        cookie_info=[{"name": "session", "issues": ["missing_secure"]}],
        robots_info={"robots_found": True, "sitemap_found": False},
        subdomains=[f"sub{i}.example.com" for i in range(20)],
    )
    codes = {f["code"] for f in findings}
    assert "missing_header" in codes
    assert "cert_expiring_soon" in codes
    assert "reputation_malicious" in codes
    assert "whois_unavailable" in codes
    assert "dns_propagation_inconsistent" in codes
    assert "cookie_flags" in codes
    assert "no_sitemap" in codes
    assert "many_subdomains" in codes
    # highest severity first
    assert findings[0]["severity"] == "high"


def test_build_findings_reports_no_issues_when_everything_is_clean():
    findings = build_findings(
        headers_info={"reachable": True, "headers": {h: "1" for h in [
            "content-security-policy", "strict-transport-security", "x-frame-options",
            "x-content-type-options", "referrer-policy", "permissions-policy",
        ]}},
        ssl_info={"valid": True, "days_remaining": 200},
        whois_info={"registrar": "Example Registrar"},
        reputation_info={"verdict": "clean"},
        dns_propagation={"consistent": True},
        cookie_info=[],
        robots_info={"robots_found": True, "sitemap_found": True},
        subdomains=[],
    )
    assert findings == [{"severity": "info", "code": "no_issues_found", "params": {}}]
