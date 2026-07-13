"""
RefreshToken table.

Each row represents one issued refresh token (i.e. roughly one login
session). Storing these server-side — instead of trusting a stateless
JWT refresh token — is what makes the following possible:

  - Logout: revoke exactly this session (set revoked_at).
  - "Log out everywhere": revoke every row for a user_id.
  - Rotation: every time a refresh token is used, it's revoked and a new
    one is issued, chained via replaced_by_token_id.
  - Theft/reuse detection: if a token that's already revoked is
    presented again, that's a strong signal it was stolen and used by
    two different parties — see auth_service.rotate_refresh_token for
    the response (revoke the whole chain / all user sessions).

Only the SHA-256 hash of the raw token is ever stored (see
core/security.py) — if this table leaked, the raw tokens couldn't be
reconstructed from it.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # SHA-256 hex digest of the raw refresh token — unique so we can look
    # up a session by exact token match in O(1) via the index.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # Lightweight session metadata — genuinely useful later for a
    # "manage your active sessions" UI, and for security auditing.
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6-safe length

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # NULL while active; set the moment this token is used-and-rotated,
    # logged out, or force-revoked (e.g. "log out everywhere").
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Points at the token that replaced this one after rotation.
    # Self-referential FK — nullable because the newest token in a chain
    # has no successor yet.
    replaced_by_token_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("refresh_tokens.id"), nullable=True
    )
