"""
Request/response schemas for the auth endpoints.

Validation lives here, not in the endpoint functions — Pydantic runs it
automatically before the endpoint code even executes, and FastAPI turns
a validation failure into a clean 422 response with field-level detail
for free.
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

_PASSWORD_MIN_LENGTH = 8
_UPPERCASE_RE = re.compile(r"[A-Z]")
_LOWERCASE_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"\d")
_SPECIAL_CHAR_RE = re.compile(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?`~|\\]")


def _validate_password_strength(password: str) -> str:
    """Shared password-strength rule used by both register and reset schemas."""
    if len(password) < _PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {_PASSWORD_MIN_LENGTH} characters long")
    if not _UPPERCASE_RE.search(password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not _LOWERCASE_RE.search(password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not _DIGIT_RE.search(password):
        raise ValueError("Password must contain at least one digit")
    if not _SPECIAL_CHAR_RE.search(password):
        raise ValueError("Password must contain at least one special character")
    return password


class UserRegisterRequest(BaseModel):
    """Body for POST /auth/register."""

    email: EmailStr
    password: str = Field(..., min_length=_PASSWORD_MIN_LENGTH, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return _validate_password_strength(value)

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Full name cannot be blank")
        return stripped


class UserLoginRequest(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    """
    Public-facing user representation — never includes hashed_password.
    `role` is included so the frontend can decide what to show (e.g.
    an Admin nav link) right after login/refresh, without a separate
    lookup — the frontend must still never TRUST this for actual
    authorization, since every protected admin action is independently
    re-checked server-side (see dependencies/auth.py::require_admin).
    Client-side role checks are for UI/UX only.
    """

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}  # allows UserResponse.model_validate(orm_user)


class AccessTokenResponse(BaseModel):
    """
    Returned by login/refresh. The refresh token itself is never included
    in this body — it travels only as an HttpOnly cookie, so client-side
    JavaScript can never read it (mitigating XSS-based token theft).
    """

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic simple-message response for actions like logout."""

    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=_PASSWORD_MIN_LENGTH, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return _validate_password_strength(value)