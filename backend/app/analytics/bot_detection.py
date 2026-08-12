"""
Heuristic-only bot signal. Per spec section 76, visitors must never be
hard-labeled as bots — only a confidence level is surfaced, and false
positives are expected (e.g. privacy-conscious browsers, corporate proxies).
"""

_BOT_MARKERS = (
    "bot",
    "spider",
    "crawl",
    "slurp",
    "curl",
    "wget",
    "python-requests",
    "python-urllib",
    "scrapy",
    "headlesschrome",
    "phantomjs",
    "monitor",
    "pingdom",
    "uptimerobot",
)


def estimate_bot_confidence(ua_string: str | None) -> str:
    if not ua_string:
        return "UNKNOWN"
    lowered = ua_string.lower()
    if any(marker in lowered for marker in _BOT_MARKERS):
        return "LIKELY_BOT"
    if len(ua_string) < 15:
        return "POSSIBLE_BOT"
    return "LIKELY_HUMAN"
