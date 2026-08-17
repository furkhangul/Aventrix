"""Cookie security analyzer: flags missing Secure/HttpOnly/SameSite attributes on Set-Cookie headers."""


def _parse_one(raw: str) -> dict:
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    name = parts[0].split("=", 1)[0] if parts else ""
    attrs = {p.split("=", 1)[0].strip().lower() for p in parts[1:]}

    samesite = None
    for p in parts[1:]:
        if p.lower().startswith("samesite="):
            samesite = p.split("=", 1)[1].strip()

    secure = "secure" in attrs
    http_only = "httponly" in attrs

    issues: list[str] = []
    if not secure:
        issues.append("missing_secure")
    if not http_only:
        issues.append("missing_httponly")
    if not samesite or samesite.lower() == "none":
        issues.append("missing_samesite")

    return {
        "name": name,
        "secure": secure,
        "http_only": http_only,
        "same_site": samesite,
        "issues": issues,
    }


def analyze_cookies(raw_set_cookie_headers: list[str]) -> list[dict]:
    return [_parse_one(raw) for raw in raw_set_cookie_headers if raw.strip()]
