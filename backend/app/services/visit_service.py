import uuid

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.bot_detection import estimate_bot_confidence
from app.analytics.user_agent import parse_ua
from app.core.security import hash_token
from app.models.link import Link
from app.models.visit import Visit
from app.services import notification_service
from app.utils.network import get_client_ip
from app.workers.queue import enqueue_visit_enrichment, enqueue_webhook_event

UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")


async def record_visit(db: AsyncSession, *, link: Link, request: Request, consent_given: bool) -> Visit:
    """
    Creates the Visit row synchronously with everything derivable from the
    request itself (fast, no external calls). IP-intelligence enrichment
    (geo/ISP/ASN/VPN signals) is filled in afterwards by a background worker
    — see dispatch_ip_enrichment() / app/workers/runner.py — so the redirect
    is never blocked on a third-party API.

    The client IP address is recorded on every visit regardless of consent;
    consent instead gates the richer device/browser/UTM fingerprint.
    """
    if not consent_given:
        visit = Visit(
            link_id=link.id,
            campaign_id=link.campaign_id,
            consent_given=False,
            ip_address=get_client_ip(request),
        )
        db.add(visit)
        await db.commit()
        await db.refresh(visit)
        await _after_visit_recorded(db, link)
        return visit

    raw_ip = get_client_ip(request)
    ua_string = request.headers.get("user-agent")
    parsed_ua = parse_ua(ua_string)

    query_utm = {k: v for k, v in request.query_params.items() if k in UTM_KEYS and v}
    utm_snapshot = query_utm or link.utm_params or None

    language = None
    accept_language = request.headers.get("accept-language")
    if accept_language:
        language = accept_language.split(",")[0].split(";")[0].strip()[:20]

    visit = Visit(
        link_id=link.id,
        campaign_id=link.campaign_id,
        consent_given=True,
        ip_address=raw_ip,
        ip_hash=hash_token(raw_ip),
        visitor_hash=hash_token(f"{raw_ip}:{link.id}"),
        browser=parsed_ua.browser,
        browser_version=parsed_ua.browser_version,
        os=parsed_ua.os,
        os_version=parsed_ua.os_version,
        device_type=parsed_ua.device_type,
        language=language,
        referrer=(request.headers.get("referer") or "")[:2048] or None,
        bot_confidence=estimate_bot_confidence(ua_string),
        utm_snapshot=utm_snapshot,
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    await _after_visit_recorded(db, link)
    return visit


async def _after_visit_recorded(db: AsyncSession, link: Link) -> None:
    """
    Fires the link.clicked webhook event (cheap, non-blocking enqueue — see
    enqueue_webhook_event) and, on the link's very first-ever visit, an
    in-app notification milestone. Wrapped defensively: nothing here may
    ever break the redirect the visitor is waiting on.
    """
    try:
        await enqueue_webhook_event(
            link.user_id, "link.clicked", {"link_id": str(link.id), "short_code": link.short_code}
        )
    except Exception:
        pass

    try:
        total = (
            await db.execute(select(func.count()).select_from(Visit).where(Visit.link_id == link.id))
        ).scalar_one()
        if total == 1:
            await notification_service.notify_link_first_visit(
                db, user_id=link.user_id, short_code=link.short_code, link_id=link.id
            )
    except Exception:
        pass


async def dispatch_ip_enrichment(visit_id: uuid.UUID, raw_ip: str) -> None:
    """Fire-and-forget: queues background IP-intelligence enrichment (see app/workers/queue.py)."""
    await enqueue_visit_enrichment(visit_id, raw_ip)
