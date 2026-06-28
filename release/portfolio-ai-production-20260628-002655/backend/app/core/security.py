"""Password hashing and JWT issuing/verification.

This module is the only place in the codebase that touches bcrypt or
jose directly, so the hashing scheme or token format can change later
without rippling through every route.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ── Passwords ────────────────────────────────────────────────────────────
# Using the `bcrypt` package directly (rather than passlib's CryptContext)
# sidesteps a long-running passlib/bcrypt version-compatibility issue and
# keeps this module's only dependency surface small and predictable.


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ── JWT access tokens ────────────────────────────────────────────────────


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a signed JWT whose `sub` claim is the user id (as a string)."""
    expire_delta = timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_at = datetime.now(timezone.utc) + expire_delta
    payload: dict[str, Any] = {"sub": subject, "exp": expire_at, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Return the subject (user id) encoded in *token*, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload.get("sub")


# ── Password reset tokens ────────────────────────────────────────────────
# These are opaque random tokens (not JWTs) stored hashed in the database
# alongside an expiry — see database/models.py:PasswordResetToken. Using a
# random token rather than a signed JWT means a leaked database row alone
# can't be replayed without also matching what was emailed to the user,
# and revocation is a single DELETE rather than a token blocklist.


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    # Reusing bcrypt here too — these are short-lived, single-use values,
    # not login credentials, but hashing at rest avoids ever storing a
    # usable secret in plaintext in the database.
    return bcrypt.hashpw(token.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_reset_token(plain_token: str, hashed_token: str) -> bool:
    return bcrypt.checkpw(plain_token.encode("utf-8"), hashed_token.encode("utf-8"))
