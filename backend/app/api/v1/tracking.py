from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.repositories.link_repository import get_link_by_short_code
from app.schemas.tracking import LinkMetaResponse, ResolveLinkRequest, ResolveLinkResponse
from app.services.link_resolution import check_link_password, is_link_usable
from app.services.visit_service import dispatch_ip_enrichment, record_visit
from app.utils.network import get_client_ip

router = APIRouter(prefix="/t", tags=["tracking"])


@router.get("/{code}/meta", response_model=LinkMetaResponse)
async def get_link_meta(code: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_short_code(db, code)
    usable, reason = is_link_usable(link)
    if not usable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=reason.value if reason else "NOT_FOUND")
    return LinkMetaResponse(needs_password=link.is_password_protected, needs_consent=link.requires_consent)


@router.post("/{code}/resolve", response_model=ResolveLinkResponse)
async def resolve_link(
    code: str,
    body: ResolveLinkRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(limit=10, window_seconds=60, scope="link-resolve")),
):
    link = await get_link_by_short_code(db, code)
    usable, reason = is_link_usable(link)
    if not usable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=reason.value if reason else "NOT_FOUND")

    if not check_link_password(link, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    consent_given = body.consent if link.requires_consent else True
    visit = await record_visit(db, link=link, request=request, consent_given=consent_given)
    if consent_given:
        await dispatch_ip_enrichment(visit.id, get_client_ip(request))
    return ResolveLinkResponse(target_url=link.target_url)
