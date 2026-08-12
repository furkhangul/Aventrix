import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_active_user
from app.core import audit_actions
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.core.security import decode_jwt
from app.models.audit_log import AuditLog
from app.models.enums import AuditResult
from app.models.user import User
from app.repositories.user_repository import get_user_by_email, get_user_by_id
from app.schemas.auth import (
    AccountDeleteRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    ProfileUpdateRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionPublic,
    TwoFactorConfirmRequest,
    TwoFactorDisableRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyLoginRequest,
    UserPublic,
    VerifyEmailRequest,
)
from app.schemas.common import PaginatedResponse
from app.services import auth_service, profile_service, session_service
from app.services.audit_service import write_audit_log
from app.utils.pagination import paginate
from app.services.exceptions import (
    AccountInactiveError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidOrExpiredTokenError,
    InvalidTwoFactorCodeError,
    NotFoundError,
    PermissionDeniedError,
    ServiceError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _service_error_to_http(exc: ServiceError) -> HTTPException:
    mapping = {
        EmailAlreadyRegisteredError: (status.HTTP_409_CONFLICT, "An account with this email already exists"),
        InvalidCredentialsError: (status.HTTP_401_UNAUTHORIZED, "Invalid email or password"),
        AccountInactiveError: (status.HTTP_403_FORBIDDEN, "This account has been disabled"),
        InvalidOrExpiredTokenError: (status.HTTP_400_BAD_REQUEST, "This link is invalid or has expired"),
        InvalidTwoFactorCodeError: (status.HTTP_401_UNAUTHORIZED, "Invalid two-factor code"),
        TwoFactorAlreadyEnabledError: (status.HTTP_409_CONFLICT, "Two-factor authentication is already enabled"),
        TwoFactorNotEnabledError: (status.HTTP_400_BAD_REQUEST, "Two-factor authentication is not enabled"),
        NotFoundError: (status.HTTP_404_NOT_FOUND, "Not found"),
        PermissionDeniedError: (status.HTTP_403_FORBIDDEN, "You do not have permission to perform this action"),
    }
    status_code, default_message = mapping.get(type(exc), (status.HTTP_400_BAD_REQUEST, str(exc) or "Request failed"))
    return HTTPException(status_code=status_code, detail=default_message)


def _session_id_from_refresh_cookie(refresh_token: str | None) -> uuid.UUID | None:
    if not refresh_token:
        return None
    payload = decode_jwt(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    try:
        return uuid.UUID(payload.get("sid"))
    except (TypeError, ValueError):
        return None


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(limit=3, window_seconds=60, scope="register")),
):
    try:
        user = await auth_service.register_user(
            db, email=body.email, password=body.password, full_name=body.full_name
        )
    except EmailAlreadyRegisteredError as exc:
        raise _service_error_to_http(exc)

    access_token, refresh_token, _session = await auth_service.create_session_and_tokens(
        db, user=user, user_agent=request.headers.get("user-agent"), ip_address=get_client_ip(request)
    )
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    await write_audit_log(
        db,
        action=audit_actions.USER_REGISTERED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    # Registration auto-logs the user in, so it counts as a login for history purposes.
    await write_audit_log(
        db,
        action=audit_actions.LOGIN_SUCCESS,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
        metadata={"via": "registration"},
    )
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(limit=5, window_seconds=60, scope="login")),
):
    try:
        user = await auth_service.authenticate_user(db, email=body.email, password=body.password)
    except (InvalidCredentialsError, AccountInactiveError) as exc:
        # Look up the account (without revealing anything in the response) so
        # a failed attempt against a real account still shows up in that
        # user's own login history / security monitoring.
        existing_user = await get_user_by_email(db, body.email)
        await write_audit_log(
            db,
            action=audit_actions.LOGIN_FAILED,
            result=AuditResult.FAILURE,
            user_id=existing_user.id if existing_user else None,
            user_email_snapshot=body.email,
            ip_address=get_client_ip(request),
        )
        raise _service_error_to_http(exc)

    if user.is_2fa_enabled:
        pending_token = auth_service.create_two_factor_pending_token(user)
        return LoginResponse(requires_2fa=True, two_factor_pending_token=pending_token)

    access_token, refresh_token, _session = await auth_service.create_session_and_tokens(
        db, user=user, user_agent=request.headers.get("user-agent"), ip_address=get_client_ip(request)
    )
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    await write_audit_log(
        db,
        action=audit_actions.LOGIN_SUCCESS,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    return LoginResponse(user=user)


@router.post("/2fa/verify-login", response_model=LoginResponse)
async def verify_login_two_factor(
    body: TwoFactorVerifyLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(limit=5, window_seconds=60, scope="2fa-login")),
):
    try:
        user_id = auth_service.resolve_two_factor_pending_user_id(body.two_factor_pending_token)
        user = await get_user_by_id(db, user_id)
        if not user:
            raise InvalidOrExpiredTokenError()
        await auth_service.verify_login_two_factor_code(db, user, body.code)
    except (InvalidOrExpiredTokenError, InvalidTwoFactorCodeError) as exc:
        raise _service_error_to_http(exc)

    access_token, refresh_token, _session = await auth_service.create_session_and_tokens(
        db, user=user, user_agent=request.headers.get("user-agent"), ip_address=get_client_ip(request)
    )
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    await write_audit_log(
        db,
        action=audit_actions.LOGIN_SUCCESS,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
        metadata={"two_factor": True},
    )
    return LoginResponse(user=user)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    if refresh_token:
        await auth_service.revoke_session_by_refresh_token(db, refresh_token)
    clear_auth_cookies(response)
    return MessageResponse(message="Logged out")


@router.post("/refresh", response_model=MessageResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session")
    try:
        access_token, new_refresh_token, _session = await auth_service.rotate_refresh_token(
            db,
            raw_refresh_token=refresh_token,
            user_agent=request.headers.get("user-agent"),
            ip_address=get_client_ip(request),
        )
    except InvalidOrExpiredTokenError as exc:
        clear_auth_cookies(response)
        raise _service_error_to_http(exc)

    set_auth_cookies(response, access_token=access_token, refresh_token=new_refresh_token)
    return MessageResponse(message="Token refreshed")


@router.get("/me", response_model=UserPublic)
async def get_me(user: User = Depends(get_current_active_user)):
    return user


@router.patch("/me", response_model=UserPublic)
async def update_me(
    body: ProfileUpdateRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    updated = await profile_service.update_profile(db, user, full_name=body.full_name)
    await write_audit_log(
        db,
        action=audit_actions.PROFILE_UPDATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    return updated


@router.post("/me/avatar", response_model=UserPublic)
async def upload_avatar(
    request: Request,
    file: UploadFile,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        updated = await profile_service.update_avatar(db, user, file)
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await write_audit_log(
        db,
        action=audit_actions.AVATAR_UPDATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    return updated


@router.delete("/me", response_model=MessageResponse)
async def delete_me(
    body: AccountDeleteRequest,
    request: Request,
    response: Response,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await write_audit_log(
        db,
        action=audit_actions.ACCOUNT_DELETED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    try:
        await auth_service.delete_account(db, user=user, password=body.password)
    except InvalidCredentialsError as exc:
        raise _service_error_to_http(exc)
    clear_auth_cookies(response)
    return MessageResponse(message="Account deleted")


@router.get("/sessions", response_model=list[SessionPublic])
async def list_sessions(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    current_session_id = _session_id_from_refresh_cookie(refresh_token)
    sessions = await session_service.list_sessions(db, user)
    return [
        SessionPublic(
            id=s.id,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            created_at=s.created_at,
            last_used_at=s.last_used_at,
            expires_at=s.expires_at,
            is_current=(s.id == current_session_id),
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await session_service.revoke_session(db, user=user, session_id=session_id)
    except (NotFoundError, PermissionDeniedError) as exc:
        raise _service_error_to_http(exc)
    await write_audit_log(
        db,
        action=audit_actions.SESSION_REVOKED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        resource_type="session",
        resource_id=str(session_id),
        ip_address=get_client_ip(request),
    )
    return MessageResponse(message="Session revoked")


@router.get("/login-history", response_model=PaginatedResponse[dict])
async def login_history(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
):
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.user_id == user.id,
            AuditLog.action.in_([audit_actions.LOGIN_SUCCESS, audit_actions.LOGIN_FAILED]),
        )
        .order_by(AuditLog.created_at.desc())
    )
    items, total = await paginate(db, stmt, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[
            {
                "action": i.action,
                "result": i.result,
                "ip_address": i.ip_address,
                "created_at": i.created_at.isoformat(),
            }
            for i in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(limit=3, window_seconds=60, scope="password-reset")),
):
    await auth_service.request_password_reset(db, body.email)
    await write_audit_log(
        db,
        action=audit_actions.PASSWORD_RESET_REQUESTED,
        result=AuditResult.SUCCESS,
        user_email_snapshot=body.email,
        ip_address=get_client_ip(request),
    )
    return MessageResponse(message="If that email is registered, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit(limit=5, window_seconds=60, scope="password-reset")),
):
    try:
        user = await auth_service.reset_password(db, token=body.token, new_password=body.new_password)
    except InvalidOrExpiredTokenError as exc:
        raise _service_error_to_http(exc)
    await session_service.revoke_all_sessions(db, user.id)
    await write_audit_log(
        db,
        action=audit_actions.PASSWORD_RESET_COMPLETED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    return MessageResponse(message="Password has been reset. Please log in again.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    try:
        await auth_service.change_password(
            db, user=user, current_password=body.current_password, new_password=body.new_password
        )
    except InvalidCredentialsError as exc:
        raise _service_error_to_http(exc)

    current_session_id = _session_id_from_refresh_cookie(refresh_token)
    await session_service.revoke_all_sessions(db, user.id, except_session_id=current_session_id)
    return MessageResponse(message="Password changed")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(body: VerifyEmailRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.verify_email(db, body.token)
    except InvalidOrExpiredTokenError as exc:
        raise _service_error_to_http(exc)
    await write_audit_log(
        db,
        action=audit_actions.EMAIL_VERIFIED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    return MessageResponse(message="Email verified")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    await auth_service.resend_verification_email(db, user)
    return MessageResponse(message="If your email isn't verified yet, a new link has been sent")


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    try:
        secret, provisioning_uri, backup_codes = await auth_service.setup_two_factor(db, user)
    except TwoFactorAlreadyEnabledError as exc:
        raise _service_error_to_http(exc)
    return TwoFactorSetupResponse(secret=secret, provisioning_uri=provisioning_uri, backup_codes=backup_codes)


@router.post("/2fa/confirm", response_model=MessageResponse)
async def confirm_two_factor(
    body: TwoFactorConfirmRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await auth_service.confirm_two_factor(db, user, body.code)
    except InvalidTwoFactorCodeError as exc:
        raise _service_error_to_http(exc)
    await write_audit_log(
        db,
        action=audit_actions.TWO_FA_ENABLED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    return MessageResponse(message="Two-factor authentication enabled")


@router.post("/2fa/disable", response_model=MessageResponse)
async def disable_two_factor(
    body: TwoFactorDisableRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await auth_service.disable_two_factor(db, user, password=body.password, code=body.code)
    except (InvalidCredentialsError, InvalidTwoFactorCodeError, TwoFactorNotEnabledError) as exc:
        raise _service_error_to_http(exc)
    await write_audit_log(
        db,
        action=audit_actions.TWO_FA_DISABLED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    return MessageResponse(message="Two-factor authentication disabled")


@router.post("/2fa/backup-codes/regenerate")
async def regenerate_backup_codes(
    request: Request, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    try:
        codes = await auth_service.regenerate_backup_codes(db, user)
    except TwoFactorNotEnabledError as exc:
        raise _service_error_to_http(exc)
    await write_audit_log(
        db,
        action=audit_actions.TWO_FA_BACKUP_CODES_REGENERATED,
        result=AuditResult.SUCCESS,
        user_id=user.id,
        user_email_snapshot=user.email,
        ip_address=get_client_ip(request),
    )
    return {"backup_codes": codes}
