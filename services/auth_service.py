from datetime import datetime, timezone, timedelta

from authlib.jose import jwt
from fastapi import HTTPException, status

from core.settings import settings
from repository.user_repository import create_user, get_user_by_email, save_refresh_token, revoke_refresh_token, get_active_refresh_tokens_for_user
from utils.hashing import hash_password, verify_password
from utils.token import create_access_token, create_refresh_token, decode_token, decode_refresh_token, decode_email_token


def register_user(db,email,password):

    # Check the user already exist or not
    existing_user = get_user_by_email(db, email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User Already Exists"
        )
    # Never store raw hashed password in DB
    hashed = hash_password(password)

    #Save the user in the Database
    user = create_user(db, email, hashed)

    return user

def login_user(db, email, password):

    user = get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification link."
        )

    access_token = create_access_token({"sub":str(user.id)})
    refresh_token = create_refresh_token({"sub" : str(user.id)})

    hashed_refresh_token = hash_password(refresh_token)
    save_refresh_token(db, user.id, hashed_refresh_token)

    return {
        "access_token" : access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



def renew_access_token(db, refresh_token: str):
    payload = decode_refresh_token(refresh_token)



    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_rows = get_active_refresh_tokens_for_user(db, int(user_id))

    matched_token = None
    for token_row in token_rows:
        if verify_password(refresh_token, token_row.token):
            matched_token = token_row
            break

    if matched_token is None:
        raise HTTPException(status_code=401, detail="Refresh token revoked or not found")

    if matched_token.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked or reused")

    if matched_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    revoke_refresh_token(db, matched_token)

    new_access_token = create_access_token({"sub": str(user_id)})
    new_refresh_token = create_refresh_token({"sub": str(user_id)})

    hashed_new_refresh_token = hash_password(new_refresh_token)
    save_refresh_token(db, int(user_id), hashed_new_refresh_token)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }



def create_email_verification_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "type": "email_verification",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.email_secret_key, algorithm="HS256")


def verify_email_token(db, token: str):
    """
    Verify email token using hybrid approach:
    1. Decode JWT (checks signature + expiry)
    2. Check DB for token validity (not used, not expired)
    3. Mark token as used
    4. Update user's is_verified flag
    """
    from models.email_verification_model import EmailVerificationToken

    # Step 1: Decode JWT using EMAIL_SECRET_KEY
    payload = decode_email_token(token)  # ← Changed from decode_refresh_token

    if payload is None or payload.get("type") != "email_verification":
        raise HTTPException(400, "Invalid or expired verification token")

    user_id = int(payload.get("sub"))

    # Step 2: Find matching token in DB (that hasn't been used)
    token_rows = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user_id,
        EmailVerificationToken.used == False,
        EmailVerificationToken.expires_at > datetime.now(timezone.utc)
    ).all()

    matched_token = None
    for token_row in token_rows:
        if verify_password(token, token_row.token):
            matched_token = token_row
            break

    if matched_token is None:
        raise HTTPException(400, "Verification token already used or expired")

    # Step 3: Get user
    from repository.user_repository import get_user_by_id
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(404, "User not found")

    if user.is_verified:
        return {"message": "Email already verified", "user": user}

    # Step 4: Mark token as used and verify user
    matched_token.used = True
    user.is_verified = True

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return {"message": "Email verified successfully", "user": user}