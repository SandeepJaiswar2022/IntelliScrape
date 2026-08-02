"""
FastAPI dependencies for protected routes.

Usage in an endpoint:

    @router.get("/me")
    async def read_me(current_user: User = Depends(get_current_active_user)):
        ...

`get_current_active_user` is what most protected endpoints should
depend on. `get_current_user` exists separately in case a future
endpoint needs the user even if inactive (rare, but keeps the door
open without re-deriving this logic).
"""

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import Role, User
from app.services.auth_service import get_user_by_id

_bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the access token from the `Authorization: Bearer
    <token>` header, then load the corresponding user.

    Edge cases handled:
      - No Authorization header at all -> 401.
      - Malformed/tampered token -> 401 (jwt.InvalidTokenError family).
      - Expired token -> 401 with a distinct message, so the frontend
        can tell "please refresh" apart from "please log in again".
      - Token's `sub` claim doesn't correspond to any existing user
        (e.g. user was deleted after the token was issued) -> 401.
    """
    if credentials is None:
        raise _unauthorized("Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Access token has expired")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid access token")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _unauthorized("Invalid access token")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise _unauthorized("User no longer exists")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Same as get_current_user, but also rejects deactivated accounts."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated",
        )
    return current_user


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Layers an ADMIN-role check on top of get_current_active_user.

    Deliberately built as "one more dependency on top of the existing
    chain" rather than a separate token-decoding path -- this is what
    guarantees an admin-only endpoint gets every check a normal
    protected endpoint gets (valid token, not expired, user still
    exists, account still active) PLUS the role check, with no
    possibility of accidentally skipping one of those checks for admin
    routes specifically.

    Role is read from the freshly-loaded `current_user` row (a normal
    DB read that already happens on every authenticated request) --
    NOT from a claim embedded in the JWT itself. That's a deliberate
    choice: embedding role in the token would mean a demoted admin
    keeps admin access until their access token naturally expires
    (up to ACCESS_TOKEN_EXPIRE_MINUTES later). Reading it fresh from
    the database means a role change takes effect on the very next
    request, at no extra query cost (the user row is already fetched).
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user