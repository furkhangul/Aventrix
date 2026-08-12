from html.parser import HTMLParser
from urllib.parse import urljoin

from app.services.exceptions import InvalidUrlError
from app.utils.safe_fetch import UnsafeUrlError, safe_fetch


class _TitleMetaParser(HTMLParser):
    """Minimal, dependency-free extractor for <title>, meta description, and favicon <link>."""

    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.description: str | None = None
        self.favicon: str | None = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (attr_dict.get("name") or attr_dict.get("property") or "").lower()
            if name in ("description", "og:description") and not self.description:
                self.description = attr_dict.get("content")
        elif tag == "link":
            rel = (attr_dict.get("rel") or "").lower()
            if "icon" in rel and not self.favicon:
                self.favicon = attr_dict.get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and not self.title:
            self.title = data.strip()


async def analyze_url(url: str) -> dict:
    try:
        result = await safe_fetch(url, method="GET")
    except UnsafeUrlError as exc:
        raise InvalidUrlError(str(exc))

    content_type = result.headers.get("content-type")
    title = description = favicon_url = None
    if content_type and "text/html" in content_type:
        parser = _TitleMetaParser()
        try:
            parser.feed(result.body.decode("utf-8", errors="ignore"))
        except Exception:
            pass
        title = parser.title
        description = parser.description
        favicon_url = urljoin(result.final_url, parser.favicon) if parser.favicon else None

    return {
        "final_url": result.final_url,
        "status_code": result.status_code,
        "redirect_count": max(0, len(result.hops) - 1),
        "elapsed_ms": result.elapsed_ms,
        "content_type": content_type,
        "title": title,
        "description": description,
        "favicon_url": favicon_url,
    }


async def check_redirects(url: str) -> dict:
    try:
        result = await safe_fetch(url, method="GET")
    except UnsafeUrlError as exc:
        raise InvalidUrlError(str(exc))

    return {
        "hops": [
            {"url": hop.url, "status_code": hop.status_code, "location": hop.location, "elapsed_ms": hop.elapsed_ms}
            for hop in result.hops
        ],
        "final_url": result.final_url,
        "final_status_code": result.status_code,
    }
