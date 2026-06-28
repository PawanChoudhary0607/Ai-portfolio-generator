"""Authentication routes: sign up, login, forgot/reset password."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    SignUpRequest,
    TokenResponse,
    UserOut,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = auth_service.sign_up(
            db, email=payload.email, password=payload.password, full_name=payload.full_name
        )
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    token = auth_service.issue_access_token(user)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = auth_service.log_in(db, email=payload.email, password=payload.password)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    token = auth_service.issue_access_token(user)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    token = auth_service.request_password_reset(db, email=payload.email)

    # Local email delivery is not configured; the reset link is
    # logged server-side so the flow is testable end-to-end locally. Wire
    # this into a real mail provider (SES, Postmark, etc.) before deploying.
    if token is not None:
        logger.info("Password reset token for %s: %s", payload.email, token)

    # Always return the same message, regardless of whether the email was
    # registered, so this endpoint can't be used to enumerate accounts.
    return MessageResponse(
        message="If an account exists for that email, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    try:
        auth_service.reset_password(db, token=payload.token, new_password=payload.new_password)
    except auth_service.InvalidResetTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MessageResponse(message="Your password has been updated. You can now log in.")

