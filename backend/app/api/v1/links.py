import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user
from app.core import audit_actions
from app.core.database import get_db
from app.models.enums import AuditResult
from app.models.link import Link
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.link import (
    LinkCreateRequest,
    LinkPublic,
    LinkSetPasswordRequest,
    LinkUpdateRequest,
    LinkWithStats,
    VisitPublic,
)
from app.services import link_service
from app.services.audit_service import write_audit_log
from app.services.exceptions import ConflictError, NotFoundError
from app.services.link_url import build_short_url

router = APIRouter(prefix="/links", tags=["links"])


def _to_public(link: Link) -> LinkPublic:
    return LinkPublic(
        id=link.id,
        campaign_id=link.campaign_id,
        campaign_name=link.campaign.name if link.campaign else None,
        campaign_status=link.campaign.status if link.campaign else None,
        short_code=link.short_code,
        short_url=build_short_url(link.short_code),
        target_url=link.target_url,
        description=link.description,
        tags=link.tags,
        is_active=link.is_active,
        expires_at=link.expires_at,
        is_password_protected=link.is_password_protected,
        requires_consent=link.requires_consent,
        utm_params=link.utm_params,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


def _to_with_stats(link: Link, stats: dict) -> LinkWithStats:
    return LinkWithStats(
        **_to_public(link).model_dump(),
        total_visits=stats.get("total_visits", 0),
        unique_visitors=stats.get("unique_visitors", 0),
    )


def _to_visit_public(visit, visit_number: int | None) -> VisitPublic:
    base = VisitPublic.model_validate(visit).model_dump(exclude={"visit_number", "is_returning_visitor"})
    return VisitPublic(
        **base,
        visit_number=visit_number,
        is_returning_visitor=bool(visit_number and visit_number > 1),
    )


@router.post("", response_model=LinkPublic, status_code=status.HTTP_201_CREATED)
async def create_link(
    body: LinkCreateRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        link = await link_service.create_link(db, user_id=user.id, data=body)
    except (NotFoundError, ConflictError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc) or "Request failed")

    await write_audit_log(
        db,
        action=audit_actions.LINK_CREATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="link",
        resource_id=str(link.id),
        ip_address=get_client_ip(request),
    )
    return _to_public(link)


@router.get("", response_model=PaginatedResponse[LinkWithStats])
async def list_links(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    campaign_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await link_service.list_links(
        db,
        user_id=user.id,
        page=page,
        page_size=page_size,
        search=search,
        campaign_id=campaign_id,
        is_active=is_active,
    )
    stats_map = await link_service.get_link_stats_map(db, [i.id for i in items])
    return PaginatedResponse(
        items=[_to_with_stats(i, stats_map.get(i.id, {})) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{link_id}", response_model=LinkWithStats)
async def get_link(
    link_id: uuid.UUID, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    try:
        link = await link_service.get_link_for_user(db, user_id=user.id, link_id=link_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    stats_map = await link_service.get_link_stats_map(db, [link.id])
    return _to_with_stats(link, stats_map.get(link.id, {}))


@router.get("/{link_id}/visits", response_model=PaginatedResponse[VisitPublic])
async def list_link_visits(
    link_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        link = await link_service.get_link_for_user(db, user_id=user.id, link_id=link_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    items, total = await link_service.list_link_visits(db, link_id=link.id, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[_to_visit_public(v, n) for v, n in items], total=total, page=page, page_size=page_size
    )


@router.patch("/{link_id}", response_model=LinkPublic)
async def update_link(
    link_id: uuid.UUID,
    body: LinkUpdateRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        link = await link_service.update_link(db, user_id=user.id, link_id=link_id, data=body)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc) or "Request failed")
    await write_audit_log(
        db,
        action=audit_actions.LINK_UPDATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="link",
        resource_id=str(link_id),
        ip_address=get_client_ip(request),
    )
    return _to_public(link)


@router.put("/{link_id}/password", response_model=LinkPublic)
async def set_link_password(
    link_id: uuid.UUID,
    body: LinkSetPasswordRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        link = await link_service.set_link_password(
            db, user_id=user.id, link_id=link_id, password=body.password
        )
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await write_audit_log(
        db,
        action=audit_actions.LINK_UPDATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="link",
        resource_id=str(link_id),
        ip_address=get_client_ip(request),
        metadata={"field": "password"},
    )
    return _to_public(link)


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await link_service.delete_link(db, user_id=user.id, link_id=link_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await write_audit_log(
        db,
        action=audit_actions.LINK_DELETED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="link",
        resource_id=str(link_id),
        ip_address=get_client_ip(request),
    )
