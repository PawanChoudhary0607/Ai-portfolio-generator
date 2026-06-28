"""Business logic for authentication. Routes stay thin; this module owns
the actual rules (uniqueness checks, token issuing, reset-token matching).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_password_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
    verify_reset_token,
)
from app.database.models import PasswordResetToken, User


class AuthError(Exception):
    """Base class for auth failures the route layer turns into HTTP responses."""


class EmailAlreadyRegisteredError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidResetTokenError(AuthError):
    pass


def sign_up(db: Session, *, email: str, password: str, full_name: str) -> User:
    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing is not None:
        raise EmailAlreadyRegisteredError(f"An account with email '{email}' already exists")

    user = User(email=email.lower(), hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def log_in(db: Session, *, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Incorrect email or password")
    if not user.is_active:
        raise InvalidCredentialsError("This account has been deactivated")
    return user


def issue_access_token(user: User) -> str:
    return create_access_token(subject=user.id)


def request_password_reset(db: Session, *, email: str) -> str | None:
    """Create a reset token for *email* if an account exists.

    Returns the plaintext token (to be emailed) or None if no account
    matches — callers must respond identically either way so the
    endpoint can't be used to enumerate registered emails.
    """
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None:
        return None

    plain_token = generate_password_reset_token()
    reset_row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(plain_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(reset_row)
    db.commit()
    return plain_token


def reset_password(db: Session, *, token: str, new_password: str) -> User:
    """Validate *token* against unused, unexpired reset rows and update
    the matching user's password.

    Tokens are opaque, so every unused/unexpired row must be checked with
    a constant-time hash comparison rather than looked up by value.
    """
    now = datetime.now(timezone.utc)
    candidates = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.used.is_(False), PasswordResetToken.expires_at > now)
        .all()
    )

    matched: PasswordResetToken | None = None
    for candidate in candidates:
        if verify_reset_token(token, candidate.token_hash):
            matched = candidate
            break

    if matched is None:
        raise InvalidResetTokenError("This password reset link is invalid or has expired")

    user = db.get(User, matched.user_id)
    if user is None:
        raise InvalidResetTokenError("This password reset link is invalid or has expired")

    user.hashed_password = hash_password(new_password)
    matched.used = True
    db.commit()
    db.refresh(user)
    return user
