"""
Lightweight technology fingerprinting from response headers, cookie names,
and a small HTML body sample. Pattern-based only — no external service, no
extra requests beyond the page fetch Security Center already makes.
"""

import re

_HEADER_SIGNATURES: list[tuple[str, str, str, re.Pattern]] = [
    # (header, category, technology, pattern)
    ("server", "web-server", "Nginx", re.compile(r"nginx", re.I)),
    ("server", "web-server", "Apache", re.compile(r"apache", re.I)),
    ("server", "web-server", "Microsoft IIS", re.compile(r"iis", re.I)),
    ("server", "web-server", "LiteSpeed", re.compile(r"litespeed", re.I)),
    ("server", "cdn", "Cloudflare", re.compile(r"cloudflare", re.I)),
    ("x-powered-by", "language", "PHP", re.compile(r"php", re.I)),
    ("x-powered-by", "language", "ASP.NET", re.compile(r"asp\.net", re.I)),
    ("x-powered-by", "framework", "Express", re.compile(r"express", re.I)),
    ("x-powered-by", "framework", "Next.js", re.compile(r"next\.js", re.I)),
]

_PRESENCE_SIGNATURES: list[tuple[str, str, str]] = [
    ("cf-ray", "cdn", "Cloudflare"),
    ("x-vercel-id", "hosting", "Vercel"),
    ("x-amz-cf-id", "cdn", "Amazon CloudFront"),
    ("x-github-request-id", "hosting", "GitHub Pages"),
    ("x-shopify-stage", "ecommerce", "Shopify"),
    ("x-drupal-cache", "cms", "Drupal"),
]

_COOKIE_SIGNATURES: dict[str, tuple[str, str]] = {
    "phpsessid": ("language", "PHP"),
    "jsessionid": ("language", "Java"),
    "laravel_session": ("framework", "Laravel"),
    "wordpress_logged_in": ("cms", "WordPress"),
    "wp-settings": ("cms", "WordPress"),
    "csrftoken": ("framework", "Django"),
    "django_language": ("framework", "Django"),
    "connect.sid": ("framework", "Express"),
    "shopify_s": ("ecommerce", "Shopify"),
}

_BODY_SIGNATURES: list[tuple[str, str, re.Pattern]] = [
    ("cms", "WordPress", re.compile(r'name="generator"\s+content="WordPress', re.I)),
    ("cms", "Joomla", re.compile(r'name="generator"\s+content="Joomla', re.I)),
    ("cms", "Drupal", re.compile(r"Drupal\.settings", re.I)),
    ("framework", "Next.js", re.compile(r"__NEXT_DATA__")),
    ("framework", "Nuxt.js", re.compile(r"__NUXT__")),
    ("framework", "React", re.compile(r"data-reactroot|react-dom")),
    ("framework", "Angular", re.compile(r"ng-version")),
    ("framework", "Vue.js", re.compile(r"data-v-app|__VUE__")),
    ("ecommerce", "Shopify", re.compile(r"cdn\.shopify\.com", re.I)),
    ("ecommerce", "WooCommerce", re.compile(r"woocommerce", re.I)),
]


def detect_technologies(headers: dict[str, str | None], cookie_names: list[str], body_sample: str) -> list[dict]:
    """headers keys are expected lowercase. Never raises. Dedupes by (category, technology)."""
    found: dict[tuple[str, str], str] = {}

    for header, category, technology, pattern in _HEADER_SIGNATURES:
        value = headers.get(header)
        if value and pattern.search(value):
            found[(category, technology)] = "header"

    for header, category, technology in _PRESENCE_SIGNATURES:
        if headers.get(header):
            found[(category, technology)] = "header"

    for cookie_name in cookie_names:
        signature = _COOKIE_SIGNATURES.get(cookie_name.lower())
        if signature:
            category, technology = signature
            found.setdefault((category, technology), "cookie")

    for category, technology, pattern in _BODY_SIGNATURES:
        if pattern.search(body_sample):
            found.setdefault((category, technology), "body")

    return [
        {"category": category, "technology": technology, "detected_via": via}
        for (category, technology), via in sorted(found.items())
    ]
