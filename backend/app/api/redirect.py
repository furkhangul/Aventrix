from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.repositories.link_repository import get_link_by_short_code
from app.services.link_resolution import is_link_usable
from app.services.visit_service import dispatch_ip_enrichment, record_visit
from app.utils.network import get_client_ip

router = APIRouter(tags=["redirect"])
settings = get_settings()


@router.get("/t/{code}")
async def resolve_short_link(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(
        rate_limit(limit=settings.rate_limit_redirect_per_minute, window_seconds=60, scope="redirect")
    ),
) -> RedirectResponse:
    link = await get_link_by_short_code(db, code)
    usable, reason = is_link_usable(link)

    if not usable:
        return RedirectResponse(
            url=f"{settings.frontend_base_url}/t/not-found?reason={reason.value}",
            status_code=302,
        )

    if link.is_password_protected or link.requires_consent:
        return RedirectResponse(url=f"{settings.frontend_base_url}/t/{code}/gate", status_code=302)

    visit = await record_visit(db, link=link, request=request, consent_given=True)
    await dispatch_ip_enrichment(visit.id, get_client_ip(request))
    return RedirectResponse(url=link.target_url, status_code=302)
