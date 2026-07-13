"""
User table.

Fields beyond the obvious (email/password) exist specifically to support
the auth edge cases this milestone handles:
  - failed_login_attempts / locked_until: per-account brute-force lockout
  - is_active: lets us disable an account without deleting data (bans,
    self-service deactivation, etc.)
  - is_verified: reserved for email verification; not enforced yet in
    this milestone (no email-sending infra wired up), but the column
    exists now so we don't need a migration later to add it.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Always store/query emails in lowercase (see auth_service) so
    # "User@Example.com" and "user@example.com" can't register twice.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Not enforced at login yet in this milestone — see README for the
    # follow-up needed (real email delivery) before enforcing it.
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Brute-force protection state ---
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Password reset state ---
    # Only the hash of the reset token is stored (same reasoning as
    # refresh tokens -- see core/security.py). Nullable because most
    # users never have a reset in flight.
    reset_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
