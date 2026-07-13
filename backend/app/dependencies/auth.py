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
from app.models.user import User
from app.services.auth_service import get_user_by_id

# `auto_error=False` lets us return our own consistent 401 body/message
# instead of FastAPI's default, and lets us distinguish "no token at
# all" from "bad token" if we ever want to log them differently.
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
