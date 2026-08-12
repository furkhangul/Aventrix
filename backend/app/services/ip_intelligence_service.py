import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.integrations.ip_intelligence.factory import get_ip_provider_chain
from app.models.ip_intelligence import IPIntelligenceCache
from app.models.visit import Visit

CACHE_TTL = timedelta(hours=24)


def _ensure_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


async def _get_or_fetch(db: AsyncSession, raw_ip: str) -> IPIntelligenceCache:
    ip_hash = hash_token(raw_ip)
    result = await db.execute(select(IPIntelligenceCache).where(IPIntelligenceCache.ip_hash == ip_hash))
    cached = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if cached and _ensure_aware(cached.expires_at) > now:
        return cached

    data = None
    provider_used = "unavailable"
    for provider in get_ip_provider_chain():
        if not provider.is_configured:
            continue
        data = await provider.lookup(raw_ip)
        if data:
            provider_used = data.provider
            break

    entry = cached or IPIntelligenceCache(ip_hash=ip_hash)
    if data:
        entry.country = data.country
        entry.country_code = data.country_code
        entry.region = data.region
        entry.city = data.city
        entry.district = data.district
        entry.timezone = data.timezone
        entry.latitude = data.latitude
        entry.longitude = data.longitude
        entry.isp = data.isp
        entry.asn = data.asn
        entry.organization = data.organization
        entry.hostname = data.hostname
        entry.is_mobile = data.is_mobile
        entry.is_vpn = data.is_vpn
        entry.is_proxy = data.is_proxy
        entry.is_tor = data.is_tor
        entry.is_hosting = data.is_hosting
    entry.provider = provider_used
    entry.fetched_at = now
    entry.expires_at = now + CACHE_TTL

    if not cached:
        db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def enrich_visit(db: AsyncSession, visit_id: uuid.UUID, raw_ip: str) -> None:
    """
    Fills in the IP-derived fields on an already-created Visit row. Called
    from the background worker (see app/workers/tasks.py) — the raw IP is
    passed through the task queue transiently and is never written to the
    database; only its salted hash (via the cache table) ever persists.
    """
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    visit = result.scalar_one_or_none()
    if not visit or not visit.consent_given:
        return

    intel = await _get_or_fetch(db, raw_ip)

    visit.country = intel.country
    visit.country_code = intel.country_code
    visit.region = intel.region
    visit.city = intel.city
    visit.district = intel.district
    visit.timezone = intel.timezone
    visit.latitude = intel.latitude
    visit.longitude = intel.longitude
    visit.isp = intel.isp
    visit.asn = intel.asn
    visit.organization = intel.organization
    visit.hostname = intel.hostname
    visit.is_mobile = intel.is_mobile
    visit.is_vpn = intel.is_vpn
    visit.is_proxy = intel.is_proxy
    visit.is_tor = intel.is_tor
    visit.is_hosting = intel.is_hosting
    await db.commit()
