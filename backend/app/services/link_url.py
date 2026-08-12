from app.core.config import get_settings

settings = get_settings()


def build_short_url(short_code: str) -> str:
    return f"{settings.tracking_base_url}/t/{short_code}"
