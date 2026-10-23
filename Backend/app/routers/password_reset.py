
import os
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session


from app.database.connection import get_db
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.core.security import hash_password
from app.core.password_reset import (
    generate_reset_token,
    hash_reset_token,
    reset_token_expiry,
)
from app.core.email_service import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Password Recovery"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == str(request.email)).first()

    # Return the same message whether or not the account exists.
    response = {
        "message": "If an account exists for this email, a reset link will be sent."
    }

    if not user:
        return response

    token = generate_reset_token()
    token_hash = hash_reset_token(token)

    # Invalidate older unused tokens for this user.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update(
        {"used_at": datetime.now(timezone.utc)},
        synchronize_session=False,
    )

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=reset_token_expiry(),
    )

    db.add(reset_record)
    db.commit()

    frontend_url = os.getenv(
        "FRONTEND_URL", "http://localhost:5173"
    ).rstrip("/")
    reset_link = (
        f"{frontend_url}/reset-password?token={quote(token)}"
    )

    
    try:
        await send_password_reset_email(str(request.email), reset_link)
    except Exception as e:
        print(f"Password reset email error: {type(e).__name__}: {e}")
        db.delete(reset_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send the reset email. Please try again later.",
        )


    return response


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 8 characters.",
        )

    token_hash = hash_reset_token(request.token)

    reset_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
        )
        .first()
    )

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already-used reset link.",
        )

    now = datetime.now(timezone.utc)
    expires_at = reset_record.expires_at

    # Handle timestamps returned by databases without timezone information.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has expired. Please request a new one.",
        )

    user = (
        db.query(User)
        .filter(User.id == reset_record.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account not found.",
        )

    try:
        user.hashed_password = hash_password(request.new_password)
        reset_record.used_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to reset password. Please try again.",
        )

    return {
        "message": "Password reset successfully. You can now log in."
    }

