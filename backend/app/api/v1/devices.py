import asyncio
import base64
import uuid
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user, require_feature
from app.core import audit_actions
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.models.enums import AuditResult, DeviceSessionStatus
from app.models.user import User
from app.repositories.device_repository import get_session_by_id
from app.schemas.common import PaginatedResponse
from app.schemas.device import (
    DevicePairingExchangeRequest,
    DevicePairingExchangeResponse,
    DevicePendingSessionResponse,
    DevicePublic,
    DeviceRenameRequest,
    DeviceSessionPublic,
    DeviceSessionStartResponse,
    DeviceSessionTokenRequest,
    DeviceWsTicketResponse,
    PairingCodeCreatedResponse,
)
from app.services import device_service, device_signaling_service, qr_service
from app.services.audit_service import write_audit_log
from app.services.exceptions import InvalidCredentialsError, InvalidOrExpiredTokenError, NotFoundError

settings = get_settings()

router = APIRouter(
    prefix="/devices", tags=["devices"], dependencies=[Depends(require_feature("enable_device_control"))]
)


def _to_public(device) -> DevicePublic:
    return DevicePublic.model_validate(device)


def _pairing_qr_data_url(code: str) -> str:
    # Same PNG generator the QR Codes module already uses (app/services/qr_service.py)
    # — pairing codes just happen to also want a scannable form.
    png_bytes = qr_service.generate_qr_png(f"aventrix-device-pair:{code}", size=320)
    return f"data:image/png;base64,{base64.b64encode(png_bytes).decode()}"


# --- Pairing -----------------------------------------------------------------


@router.post("/pairing-codes", response_model=PairingCodeCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_pairing_code(
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(5, 300, scope="device_pairing_gen")),
):
    pairing, code = await device_service.create_pairing_code(db, user_id=user.id)
    await write_audit_log(
        db,
        action=audit_actions.DEVICE_PAIRING_CODE_GENERATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="device_pairing_code",
        resource_id=str(pairing.id),
        ip_address=get_client_ip(request),
    )
    return PairingCodeCreatedResponse(
        code=code, expires_at=pairing.expires_at, qr_code_data_url=_pairing_qr_data_url(code)
    )


@router.post("/pairing-codes/{code}/exchange", response_model=DevicePairingExchangeResponse)
async def exchange_pairing_code(
    code: str,
    body: DevicePairingExchangeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(10, 300, scope="device_pairing_exchange")),
):
    """
    Called by the (future) Android client, not a web session — the pairing
    code is itself the credential, since the phone has no browser session
    at this point. No get_current_active_user dependency by design; the
    tight rate limit above plus the code's short TTL are this endpoint's
    actual defense against brute force (see docs/SECURITY.md).
    """
    if code != body.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code mismatch")
    try:
        device, device_secret = await device_service.exchange_pairing_code(
            db,
            code=body.code,
            device_name=body.device_name,
            device_fingerprint=body.device_fingerprint,
            platform=body.platform,
        )
    except InvalidOrExpiredTokenError as exc:
        await write_audit_log(
            db,
            action=audit_actions.DEVICE_PAIRING_FAILED,
            result=AuditResult.FAILURE,
            resource_type="device_pairing_code",
            ip_address=get_client_ip(request),
            metadata={"reason": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await write_audit_log(
        db,
        action=audit_actions.DEVICE_PAIRED,
        result=AuditResult.SUCCESS,
        user_id=device.user_id,
        resource_type="device",
        resource_id=str(device.id),
        ip_address=get_client_ip(request),
    )
    return DevicePairingExchangeResponse(device=_to_public(device), device_secret=device_secret)


async def _device_secret_from_header(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing device credential",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ", 1)[1]


@router.post("/{device_id}/sessions/token", response_model=DeviceWsTicketResponse)
async def issue_device_session_token(
    device_id: uuid.UUID,
    body: DeviceSessionTokenRequest,
    device_secret: str = Depends(_device_secret_from_header),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(20, 300, scope="device_session_token")),
):
    """
    Lets a paired device turn its persisted secret into a signaling ticket
    for a session the controller side already started via POST
    /{device_id}/sessions. Only Phase D's Android client calls this in
    practice; it's shipped now so the pairing/session contract is complete
    and independently testable (see docs/DEVICE_CONTROL_PROTOCOL.md).
    """
    try:
        ticket, ice_servers = await device_service.issue_device_ticket(
            db, device_id=device_id, device_secret=device_secret, session_id=body.session_id
        )
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credential")
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    except InvalidOrExpiredTokenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return DeviceWsTicketResponse(ticket=ticket, ice_servers=ice_servers, expires_in=settings.device_ws_ticket_ttl_seconds)


@router.get("/{device_id}/sessions/pending", response_model=DevicePendingSessionResponse)
async def get_pending_device_session(
    device_id: uuid.UUID,
    device_secret: str = Depends(_device_secret_from_header),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(30, 60, scope="device_session_poll")),
):
    """
    Lets a paired device discover that the web/controller side started a
    session, before it knows the session_id that /sessions/token requires.
    Polled periodically by the Android client while sharing is enabled —
    see docs/DEVICE_CONTROL_PROTOCOL.md.
    """
    try:
        session_id = await device_service.get_pending_session(db, device_id=device_id, device_secret=device_secret)
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credential")
    return DevicePendingSessionResponse(session_id=session_id)


# --- Devices -------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[DevicePublic])
async def list_devices(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await device_service.list_devices(db, user_id=user.id, page=page, page_size=page_size)
    return PaginatedResponse(items=[_to_public(d) for d in items], total=total, page=page, page_size=page_size)


@router.patch("/{device_id}", response_model=DevicePublic)
async def rename_device(
    device_id: uuid.UUID,
    body: DeviceRenameRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        device = await device_service.rename_device(db, user_id=user.id, device_id=device_id, name=body.name)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    await write_audit_log(
        db,
        action=audit_actions.DEVICE_RENAMED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="device",
        resource_id=str(device_id),
        ip_address=get_client_ip(request),
    )
    return _to_public(device)


@router.post("/{device_id}/revoke", response_model=DevicePublic)
async def revoke_device(
    device_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        device = await device_service.revoke_device(db, user_id=user.id, device_id=device_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    await write_audit_log(
        db,
        action=audit_actions.DEVICE_REVOKED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="device",
        resource_id=str(device_id),
        ip_address=get_client_ip(request),
    )
    return _to_public(device)


# --- Sessions ------------------------------------------------------------------


@router.get("/{device_id}/sessions", response_model=PaginatedResponse[DeviceSessionPublic])
async def list_device_sessions(
    device_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        items, total = await device_service.list_device_sessions(
            db, user_id=user.id, device_id=device_id, page=page, page_size=page_size
        )
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return PaginatedResponse(
        items=[DeviceSessionPublic.model_validate(s) for s in items], total=total, page=page, page_size=page_size
    )


@router.post("/{device_id}/sessions", response_model=DeviceSessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    device_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session, web_ticket, ice_servers = await device_service.start_session(db, user_id=user.id, device_id=device_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    await write_audit_log(
        db,
        action=audit_actions.DEVICE_SESSION_STARTED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="device_session",
        resource_id=str(session.id),
        ip_address=get_client_ip(request),
    )
    return DeviceSessionStartResponse(
        session_id=session.id, web_ticket=web_ticket, ice_servers=ice_servers, expires_at=session.expires_at
    )


@router.post("/{device_id}/sessions/{session_id}/end", response_model=DeviceSessionPublic)
async def end_session(
    device_id: uuid.UUID,
    session_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await device_service.end_session(db, user_id=user.id, device_id=device_id, session_id=session_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await write_audit_log(
        db,
        action=audit_actions.DEVICE_SESSION_ENDED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="device_session",
        resource_id=str(session_id),
        ip_address=get_client_ip(request),
    )
    return DeviceSessionPublic.model_validate(session)


# --- Signaling -------------------------------------------------------------------

WS_POLICY_VIOLATION = 4401
WS_NOT_FOUND = 4404


@router.websocket("/sessions/{session_id}/signal")
async def device_signal(
    websocket: WebSocket,
    session_id: uuid.UUID,
    ticket: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Relays WebRTC SDP offer/answer and ICE candidate JSON between the two
    peers of a session (see docs/DEVICE_CONTROL_PROTOCOL.md for the exact
    envelope). No media of any kind passes through this process — only
    this small signaling handshake — via app.services.device_signaling_service's
    Redis pub/sub relay.
    """
    try:
        claims = await device_service.validate_ws_ticket(ticket, expected_session_id=session_id)
    except InvalidOrExpiredTokenError:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return

    session = await get_session_by_id(db, session_id)
    now = datetime.now(timezone.utc)
    if not session or device_service.as_aware_utc(session.expires_at) < now or session.status == DeviceSessionStatus.ENDED:
        await websocket.close(code=WS_NOT_FOUND)
        return

    role = claims["role"]
    peer_role = device_signaling_service.other_role(role)
    await websocket.accept()
    await device_service.mark_session_active_on_connect(db, session_id=session_id, role=role)

    # Tell whoever is (or later shows up) on the other side that this peer is
    # here. The controller needs it to distinguish "the phone has not joined
    # yet" from "the phone joined and negotiation is under way" — without it
    # the browser can only show an indefinite spinner and has no idea whether
    # anything is wrong.
    await device_signaling_service.publish_to_role(
        session_id, peer_role, {"type": "peer-joined", "data": {"role": role}}
    )

    async def forward_from_peer():
        async with device_signaling_service.SignalRelay(session_id, role) as relay:
            async for message in relay.listen():
                await websocket.send_json(message)

    async def forward_to_peer():
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict) or "type" not in message:
                continue
            await device_signaling_service.publish_signal(session_id, role, message)
            if message.get("type") == "bye":
                break

    tasks = [asyncio.create_task(forward_from_peer()), asyncio.create_task(forward_to_peer())]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            exc = task.exception()
            if exc and not isinstance(exc, WebSocketDisconnect):
                raise exc
    finally:
        # Either peer leaving ends the session: the controller is the only
        # thing driving it, and the target is the only thing producing media,
        # so neither can usefully carry on alone. Say so on the way out
        # instead of letting the survivor hang on a dead connection.
        try:
            await device_signaling_service.publish_to_role(
                session_id, peer_role, {"type": "peer-left", "data": {"role": role}}
            )
        except Exception:
            pass
        await device_service.mark_session_ended(db, session_id=session_id, reason="disconnected")
