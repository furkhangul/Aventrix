import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.domain_intel.dns_lookup import lookup_dns
from app.integrations.domain_intel.ssl_check import check_ssl
from app.integrations.domain_intel.whois_lookup import lookup_whois
from app.integrations.reputation.factory import get_reputation_provider_chain
from app.models.security_scan import SecurityScan
from app.repositories.security_scan_repository import get_owned_scan
from app.services import notification_service
from app.services.exceptions import InvalidUrlError, NotFoundError
from app.utils.pagination import paginate
from app.utils.safe_fetch import UnsafeUrlError, safe_fetch, validate_hostname_for_connect
from app.workers.queue import enqueue_webhook_event

settings = get_settings()

SECURITY_HEADERS = [
    "content-security-policy",
    "strict-transport-security",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
]


def _normalize_domain(raw: str) -> str:
    domain = raw.strip().lower()
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix) :]
    return domain.split("/")[0].split(":")[0]


async def _check_headers(domain: str) -> dict:
    try:
        result = await safe_fetch(f"https://{domain}/", method="GET")
    except UnsafeUrlError as exc:
        return {"reachable": False, "error": str(exc), "headers": {}}

    return {
        "reachable": True,
        "status_code": result.status_code,
        "headers": {header: result.headers.get(header) for header in SECURITY_HEADERS},
    }


def _score_headers(headers_info: dict) -> int:
    if not headers_info.get("reachable"):
        return 0
    present = headers_info.get("headers", {})
    weight_each = 100 / len(SECURITY_HEADERS)
    return round(min(sum(weight_each for value in present.values() if value), 100))


def _score_ssl(ssl_info: dict | None) -> int:
    if not ssl_info or not ssl_info.get("valid"):
        return 0
    days = ssl_info.get("days_remaining")
    if days is None:
        return 50
    if days < 0:
        return 0
    if days < 14:
        return 40
    if days < 30:
        return 70
    return 100


def _score_reputation(reputation_info: dict | None) -> int:
    if not reputation_info:
        return 100  # unknown is treated neutrally, not penalized
    return {"clean": 100, "suspicious": 40, "malicious": 0}.get(reputation_info.get("verdict"), 100)


def _compute_score(headers_info: dict, ssl_info: dict | None, reputation_info: dict | None) -> int:
    # Weighted per spec sections 19/20: headers 35%, SSL 35%, reputation 30%.
    return round(
        _score_headers(headers_info) * 0.35 + _score_ssl(ssl_info) * 0.35 + _score_reputation(reputation_info) * 0.30
    )


async def run_scan(db: AsyncSession, *, user_id: uuid.UUID, domain: str) -> SecurityScan:
    domain = _normalize_domain(domain)
    if not domain or "." not in domain:
        raise InvalidUrlError("A valid domain is required")

    try:
        await validate_hostname_for_connect(domain)
    except UnsafeUrlError as exc:
        raise InvalidUrlError(str(exc))

    dns_records = await lookup_dns(domain)
    whois_info = await lookup_whois(domain)
    ssl_info = await check_ssl(domain)
    headers_info = await _check_headers(domain)

    reputation_info = None
    for provider in get_reputation_provider_chain():
        if not provider.is_configured:
            continue
        result = await provider.check(domain)
        if result:
            reputation_info = {"verdict": result.verdict, "categories": result.categories, "provider": result.provider}
            break

    score = _compute_score(headers_info, ssl_info, reputation_info)

    scan = SecurityScan(
        user_id=user_id,
        domain=domain,
        score=score,
        ssl_info=ssl_info,
        dns_records=dns_records,
        whois_info=whois_info,
        headers_info=headers_info,
        reputation_info=reputation_info,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    if score < settings.security_scan_alert_threshold:
        await enqueue_webhook_event(
            user_id, "security.alert", {"domain": domain, "score": score, "scan_id": str(scan.id)}
        )
        await notification_service.notify_security_scan_warning(
            db, user_id=user_id, domain=domain, score=score, scan_id=scan.id
        )

    return scan


async def list_scans(
    db: AsyncSession, *, user_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[SecurityScan], int]:
    stmt = select(SecurityScan).where(SecurityScan.user_id == user_id).order_by(SecurityScan.created_at.desc())
    return await paginate(db, stmt, page=page, page_size=page_size)


async def get_scan_for_user(db: AsyncSession, *, user_id: uuid.UUID, scan_id: uuid.UUID) -> SecurityScan:
    scan = await get_owned_scan(db, user_id=user_id, scan_id=scan_id)
    if not scan:
        raise NotFoundError()
    return scan
