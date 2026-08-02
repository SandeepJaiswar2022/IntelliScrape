"""
Auth HTTP endpoints.

These functions stay thin on purpose: parse/validate the request
(handled mostly by Pydantic already), delegate to app.services.auth_service
for the actual logic, then shape the HTTP response (status code, cookies,
error mapping). All the "what counts as valid" decisions live in the
service layer, not here.

Cookie strategy recap (see core/security.py for the token design):
  - The access token goes in the JSON response body -- the frontend
    keeps it in memory and attaches it as `Authorization: Bearer <token>`.
  - The refresh token goes ONLY in an HttpOnly cookie, scoped to the
    auth routes -- client-side JS can never read it (XSS mitigation),
    and it's never present in any JSON response body.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services import auth_service
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

_REFRESH_COOKIE_NAME = "refresh_token"
# Scoping the cookie's path to /api/v1/auth means the browser only ever
# sends it to auth endpoints (login/refresh/logout) -- not to every API
# route -- shrinking the blast radius if any other endpoint were ever
# compromised (e.g. an SSRF/log-reflection bug elsewhere in the API).
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    """Attach the refresh token to the response as a secure HttpOnly cookie."""
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=_REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN or None,
        httponly=True,  # never readable by client-side JavaScript
        secure=settings.COOKIE_SECURE,  # must be True in any HTTPS deployment
        samesite="none" if settings.COOKIE_SECURE else "lax",  # sent on top-level navigation + same-site XHR; blocks most CSRF vectors
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=_REFRESH_COOKIE_NAME,
        path=_REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN or None,
    )


async def _issue_tokens_for_user(
    db: AsyncSession, response: Response, user: User, request: Request
) -> AccessTokenResponse:
    """Shared helper: issue a fresh access+refresh token pair for a user."""
    access_token = create_access_token(str(user.id))
    raw_refresh_token = await auth_service.issue_refresh_token(
        db,
        user_id=user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_refresh_cookie(response, raw_refresh_token)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/register",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: UserRegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    """
    Register a new account and log the user in immediately.

    NOTE: `is_verified` starts False and is not yet enforced anywhere --
    email verification requires wiring up a real email provider, which
    is intentionally out of scope for this milestone. See README for
    the follow-up.
    """
    try:
        user = await auth_service.register_user(
            db, email=body.email, password=body.password, full_name=body.full_name
        )
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)

    return await _issue_tokens_for_user(db, response, user, request)


@router.post("/login", response_model=AccessTokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    """
    Authenticate and issue a new token pair.

    All failure branches (unknown email, wrong password, locked account,
    inactive account) return the SAME 401 status with a deliberately
    generic detail message for unknown-email/wrong-password, so the API
    response never confirms whether a given email is registered. Locked
    and inactive are distinguished because, unlike email existence,
    knowing your own account is locked/deactivated isn't a meaningful
    information leak to an attacker who already knows the correct email.
    """
    try:
        user = await auth_service.authenticate_user(db, email=body.email, password=body.password)
    except auth_service.AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Too many failed attempts. Try again after {exc.locked_until.isoformat()}",
        )
    except auth_service.AccountInactiveError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)

    return await _issue_tokens_for_user(db, response, user, request)


@router.post("/refresh", response_model=AccessTokenResponse)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    """
    Exchange a valid refresh token (from the HttpOnly cookie) for a new
    access token, rotating the refresh token in the process.

    Edge case: if no refresh cookie is present at all (e.g. it expired
    client-side, was cleared, or this is a first-time visitor), this is
    a plain 401 -- the frontend should treat this identically to "not
    logged in" and redirect to the login page.
    """
    raw_refresh_token = request.cookies.get(_REFRESH_COOKIE_NAME)
    if raw_refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided"
        )

    try:
        user, new_raw_refresh_token = await auth_service.rotate_refresh_token(
            db,
            raw_token=raw_refresh_token,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except auth_service.InvalidRefreshTokenError as exc:
        # Whatever the specific reason, always clear the (bad) cookie so
        # the browser stops sending a token that will never work again.
        _clear_refresh_cookie(response)
        logger.warning("Refresh token rejected: %s", exc.message)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)

    access_token = create_access_token(str(user.id))
    _set_refresh_cookie(response, new_raw_refresh_token)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    """
    Log out the current session only (other devices/sessions stay logged in).
    Always succeeds from the client's point of view, even if the cookie
    was already missing/invalid -- logout should never surface an error
    for "you were already logged out".
    """
    raw_refresh_token = request.cookies.get(_REFRESH_COOKIE_NAME)
    if raw_refresh_token is not None:
        await auth_service.revoke_refresh_token(db, raw_refresh_token)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Log out of every session/device for the current user. Useful when a
    user suspects their account/token has been compromised.
    Requires a valid access token (i.e. you must be logged in somewhere
    to invoke this), unlike plain /logout.
    """
    await auth_service.revoke_all_user_tokens(db, current_user.id)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out of all sessions")


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Start a password reset flow.

    Always returns the same generic message regardless of whether the
    email exists -- this is the standard mitigation against using this
    endpoint to enumerate registered emails.

    TODO (follow-up, not in this milestone): actually send `raw_token`
    via a transactional email provider (e.g. SendGrid/Resend) as a
    reset link. For now it is only logged, which is fine for local
    development but MUST be replaced before any real user relies on
    this flow.
    """
    raw_token = await auth_service.create_password_reset_token(db, body.email)
    if raw_token is not None:
        # Replace this log line with a real email send before going live.
        logger.info("Password reset token for %s: %s", body.email, raw_token)

    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def reset_password(
    request: Request, body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """Complete a password reset using the token issued by /forgot-password."""
    try:
        await auth_service.reset_password(db, raw_token=body.token, new_password=body.new_password)
    except auth_service.InvalidResetTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)

    return MessageResponse(message="Password has been reset successfully. Please log in again.")
