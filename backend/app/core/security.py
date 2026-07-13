"""
All cryptographic primitives used by auth live here, and nowhere else.
Keeping hashing/token logic in one module makes it easy to audit and
means every other file just calls these functions instead of rolling
its own crypto.

Two different token strategies are used deliberately:

  1. ACCESS TOKEN — a short-lived, stateless JWT. It authorizes API
     calls and is never stored server-side. Because it's stateless,
     it can't be revoked before it expires — which is exactly why it's
     kept short-lived (15 min default).

  2. REFRESH TOKEN — a long-lived, opaque random string (NOT a JWT).
     Only its SHA-256 hash is stored in the database. This lets us:
       - revoke a single session (delete/mark its row)
       - revoke every session for a user (delete/mark all their rows)
       - detect refresh-token theft (see auth_service.rotate_refresh_token)
     None of that is possible with a purely stateless JWT refresh token,
     which is why we don't use one here.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

# --- Password hashing (Argon2id) ---
# Argon2 is the winner of the 2015 Password Hashing Competition and is
# the current recommended algorithm (stronger against GPU/ASIC cracking
# than bcrypt for equivalent tuning). argon2-cffi is actively maintained,
# unlike the now-unmaintained `passlib` library many older tutorials use.
_password_hasher = PasswordHasher()

# A fixed dummy hash used only for timing-attack mitigation during login
# (see auth_service.authenticate_user for why this exists).
_DUMMY_HASH_FOR_TIMING_SAFETY = _password_hasher.hash("not-a-real-password")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store plaintext, ever."""
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored hash.
    Returns False on any mismatch instead of raising, so callers can
    treat this as a simple boolean check.
    """
    try:
        _password_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def dummy_verify_for_timing_safety(plain_password: str) -> None:
    """
    Run a throwaway password verification against a fixed dummy hash.

    Why this exists: if we only call verify_password() when a user
    exists, and skip it entirely when the email isn't found, an attacker
    can measure response times to learn which emails are registered
    (verification takes measurably longer than an early "not found"
    return). Calling this in the "user not found" branch keeps response
    times consistent regardless of whether the email exists.
    """
    try:
        _password_hasher.verify(_DUMMY_HASH_FOR_TIMING_SAFETY, plain_password)
    except VerifyMismatchError:
        pass


# --- JWT access tokens ---

def create_access_token(user_id: str) -> str:
    """
    Create a short-lived JWT access token for a given user id.

    Claims:
      sub  - subject, the user's id (standard JWT claim)
      type - "access", so a refresh token or other token type can never
             be mistaken for / misused as an access token
      jti  - unique token id (useful if we ever add access-token
             blacklisting; harmless to include now)
      iat  - issued-at
      exp  - expiry, enforced automatically by the jwt library on decode
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Raises jwt.ExpiredSignatureError if expired, or jwt.InvalidTokenError
    (or a subclass) for any other malformed/invalid/tampered token.
    Callers (see dependencies/auth.py) are expected to catch these and
    turn them into a 401 response.
    """
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        # Defends against a refresh token (or any other token type) being
        # replayed against an endpoint that expects an access token.
        raise jwt.InvalidTokenError("Token is not an access token")
    return payload


# --- Opaque refresh tokens ---

def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure, URL-safe random refresh token.
    This is the raw token sent to the client (via HttpOnly cookie) —
    the database only ever stores its hash, never this raw value.
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw_token: str) -> str:
    """
    Hash a refresh token for storage/lookup.

    SHA-256 (not Argon2) is intentional here: this token is already a
    high-entropy random value (not a human-memorable password), so it
    doesn't need a slow, salted password-hashing algorithm — it needs a
    fast, deterministic hash so we can look it up by exact match in the
    database on every refresh request.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
