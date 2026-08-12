from dataclasses import dataclass

from user_agents import parse as parse_user_agent


@dataclass
class ParsedUserAgent:
    browser: str | None
    browser_version: str | None
    os: str | None
    os_version: str | None
    device_type: str | None


def parse_ua(ua_string: str | None) -> ParsedUserAgent:
    if not ua_string:
        return ParsedUserAgent(None, None, None, None, None)

    ua = parse_user_agent(ua_string)

    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "other"

    return ParsedUserAgent(
        browser=ua.browser.family or None,
        browser_version=ua.browser.version_string or None,
        os=ua.os.family or None,
        os_version=ua.os.version_string or None,
        device_type=device_type,
    )
