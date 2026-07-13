"""
Auth business logic.

Endpoint functions (app/api/v1/endpoints/auth.py) stay thin — they parse
the request, call into this module, and shape the HTTP response. All the
actual decision-making (is this login allowed? is this token still
valid? should this account be locked?) lives here so it's testable
independent of FastAPI/HTTP concerns.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    dummy_verify_for_timing_safety,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User


class AuthError(Exception):
    """
    Base class for expected auth failures (bad credentials, locked
    account, expired/reused token, etc).

    Endpoints catch this and turn it into the appropriate HTTP status —
    keeping HTTP status codes out of the service layer keeps this module
    reusable outside of a web context (e.g. from a CLI script or test).
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EmailAlreadyRegisteredError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class AccountLockedError(AuthError):
    def __init__(self, locked_until: datetime):
        self.locked_until = locked_until
        super().__init__(f"Account locked until {locked_until.isoformat()}")


class AccountInactiveError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


class InvalidResetTokenError(AuthError):
    pass


# --- Lookups ---

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email. Callers are responsible for lowercasing first."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# --- Registration ---

async def register_user(db: AsyncSession, email: str, password: str, full_name: str) -> User:
    """
    Create a new user.

    Edge case handled: email is normalized to lowercase before the
    uniqueness check and before storage, so "Foo@Bar.com" and
    "foo@bar.com" can never both register -- Postgres' unique index on
    a raw string wouldn't catch that on its own.
    """
    normalized_email = email.strip().lower()

    existing_user = await get_user_by_email(db, normalized_email)
    if existing_user is not None:
        # Deliberately generic message -- avoids confirming whether a
        # *different* email is registered elsewhere in the system, while
        # still being clear about why *this* request failed. This is a
        # reasonable trade-off for a register endpoint (unlike login,
        # where we hide this entirely -- see authenticate_user).
        raise EmailAlreadyRegisteredError("An account with this email already exists")

    user = User(
        email=normalized_email,
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# --- Login / authentication ---

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """
    Validate credentials and enforce brute-force lockout.

    Edge cases handled here:
      1. Unknown email: run a dummy password verification anyway (see
         core/security.dummy_verify_for_timing_safety) so response time
         doesn't leak whether the email is registered, then raise the
         *same* InvalidCredentialsError as a wrong-password case. The
         endpoint returns an identical 401 message for both, preventing
         user enumeration via error content.
      2. Account locked: if locked_until is in the future, reject
         immediately without even checking the password -- this both
         protects against continued brute-forcing and avoids doing
         expensive Argon2 verification for a login we're going to
         reject anyway.
      3. Wrong password: increment failed_login_attempts. If this push
         it over MAX_FAILED_LOGIN_ATTEMPTS, lock the account for
         ACCOUNT_LOCKOUT_MINUTES.
      4. Correct password: reset failed_login_attempts/locked_until back
         to a clean state (a successful login clears past failures).
      5. Inactive account: rejected even with correct credentials --
         checked *after* password verification so we don't reveal
         account status to someone who doesn't actually know the
         password.
    """
    normalized_email = email.strip().lower()
    user = await get_user_by_email(db, normalized_email)

    if user is None:
        dummy_verify_for_timing_safety(password)
        raise InvalidCredentialsError("Incorrect email or password")

    # Lockout check happens before password verification (cheap check
    # first) -- no point paying Argon2's cost for a login we'll reject.
    now = datetime.now(timezone.utc)
    if user.locked_until is not None and user.locked_until > now:
        raise AccountLockedError(user.locked_until)

    if not verify_password(password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
            user.failed_login_attempts = 0  # lockout window itself is now the deterrent
        await db.commit()
        raise InvalidCredentialsError("Incorrect email or password")

    if not user.is_active:
        raise AccountInactiveError("This account has been deactivated")

    # Successful login -- clear any prior failure state.
    if user.failed_login_attempts != 0 or user.locked_until is not None:
        user.failed_login_attempts = 0
        user.locked_until = None
        await db.commit()

    return user


# --- Refresh token issuance / rotation / revocation ---

async def issue_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_agent: str | None,
    ip_address: str | None,
) -> str:
    """
    Create a new refresh token row and return the RAW token (only this
    function ever sees the raw value before it's hashed for storage --
    the caller is responsible for putting it straight into an HttpOnly
    cookie and never logging or returning it in a JSON body).
    """
    raw_token = generate_refresh_token()
    token_row = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(token_row)
    await db.commit()
    return raw_token


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[User, str]:
    """
    Validate a presented refresh token and issue a new one in its place
    (rotation). Returns (user, new_raw_refresh_token).

    Edge cases handled:
      1. Token not found at all -> invalid (never issued, or already
         pruned/expired-and-deleted).
      2. Token expired -> invalid, even if otherwise unrevoked.
      3. Token already revoked -> this is the theft-detection case: a
         legitimate client only ever presents each refresh token once
         (rotation immediately revokes it). If a *revoked* token is
         presented again, either (a) the same client retried a stale
         request, or (b) an attacker has a copy of a token that the
         legitimate user already rotated past. We can't distinguish
         these cases, so we fail safe: revoke the user's ENTIRE
         session chain, forcing a fresh login everywhere. This is the
         standard "refresh token reuse detection" pattern.
      4. User no longer active -> invalid, even with a technically
         valid token (covers accounts deactivated after the token was
         issued).
    """
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()

    if token_row is None:
        raise InvalidRefreshTokenError("Refresh token is invalid")

    now = datetime.now(timezone.utc)

    if token_row.revoked_at is not None:
        # Reuse of an already-rotated token -- possible theft.
        # Fail safe: nuke every active session for this user.
        await revoke_all_user_tokens(db, token_row.user_id)
        raise InvalidRefreshTokenError(
            "Refresh token has already been used -- all sessions have been revoked as a precaution"
        )

    if token_row.expires_at < now:
        raise InvalidRefreshTokenError("Refresh token has expired")

    user = await get_user_by_id(db, token_row.user_id)
    if user is None or not user.is_active:
        raise InvalidRefreshTokenError("Refresh token is invalid")

    # Rotate: revoke the presented token and issue a fresh one, chained
    # via replaced_by_token_id so the history is auditable.
    new_raw_token = generate_refresh_token()
    new_token_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_raw_token),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_token_row)
    await db.flush()  # ensures new_token_row.id is populated before we reference it

    token_row.revoked_at = now
    token_row.replaced_by_token_id = new_token_row.id

    await db.commit()
    return user, new_raw_token


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    """
    Revoke a single refresh token (used for logout). Silently succeeds
    even if the token doesn't exist/is already revoked -- logout should
    never fail loudly just because the session was already gone.
    """
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()
    if token_row is not None and token_row.revoked_at is None:
        token_row.revoked_at = datetime.now(timezone.utc)
        await db.commit()


async def revoke_all_user_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    """
    Revoke every active refresh token for a user ("log out everywhere").
    Used both as an explicit user action and internally as the response
    to suspected refresh-token theft (see rotate_refresh_token).
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
    )
    for token_row in result.scalars().all():
        token_row.revoked_at = now
    await db.commit()


# --- Password reset ---

async def create_password_reset_token(db: AsyncSession, email: str) -> str | None:
    """
    Generate a password reset token for the given email.

    Returns None if no account exists for that email -- the endpoint
    layer deliberately ignores this distinction in its response (always
    replies with the same generic message) so the API never confirms or
    denies whether an email is registered.
    """
    normalized_email = email.strip().lower()
    user = await get_user_by_email(db, normalized_email)
    if user is None:
        return None

    raw_token = generate_refresh_token()  # reusing the same secure generator; unrelated table
    user.reset_token_hash = hash_refresh_token(raw_token)
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.commit()

    # NOTE (follow-up work, not in this milestone): send `raw_token` via
    # a real email provider (e.g. SendGrid/Resend) as a link like
    # https://app.intelliscrape.com/reset-password?token=<raw_token>
    # For now we only return it to the caller, who logs it -- see the
    # endpoint for the explicit TODO.
    return raw_token


async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> None:
    """
    Complete a password reset.

    Edge cases handled:
      - Token doesn't match any user, or has expired -> InvalidResetTokenError.
      - On success: the reset token is cleared (single-use) and, as a
        security best practice, every existing refresh token for the
        user is revoked -- a password reset should force re-login on
        every device, including whatever device an attacker may have
        been using with a stolen session.
    """
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(select(User).where(User.reset_token_hash == token_hash))
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if (
        user is None
        or user.reset_token_expires_at is None
        or user.reset_token_expires_at < now
    ):
        raise InvalidResetTokenError("Password reset token is invalid or has expired")

    user.hashed_password = hash_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    # Also clear any lockout state -- a successful password reset is a
    # strong proof of ownership and shouldn't stay locked out.
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()

    await revoke_all_user_tokens(db, user.id)
