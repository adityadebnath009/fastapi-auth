from fastapi import HTTPException
from fastapi import Response
from fastapi import APIRouter
from fastapi.params import Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core import settings
from database.dependencies import get_db
from repository.user_repository import revoke_refresh_token, get_active_refresh_tokens_for_user, get_user_by_id, \
    save_verification_token_to_db, get_user_by_email
from services.auth_service import register_user, login_user, renew_access_token, create_email_verification_token, \
    verify_email_token
from utils.auth_dependency import get_current_user

from schemas.user_schemas import UserCreate
from services.email_service import send_email
from utils.hashing import verify_password
from utils.token import decode_refresh_token
from core.settings import settings
router = APIRouter(prefix="/auth", tags=["auth"])




@router.post("/register")
def register(user: UserCreate,  db:Session = Depends(get_db)):

    user = register_user(db, user.email, user.password)
    token = create_email_verification_token(user.id)
    save_verification_token_to_db(db, user.id, token)
    verification_link = f"{settings.backend_url}/auth/verify-email?token={token}"

    body = f"""
        <html>
            <body>
                <h2>Welcome! Please verify your email</h2>
                <p>Click the link below to verify your email address:</p>
                <a href="{verification_link}">Verify Email</a>
                <p style="margin-top: 20px; color: #999;">This link expires in 24 hours.</p>
            </body>
        </html>
        """


    send_email(
        to_email=user.email,
        subject="Verify your email",
        body=body
    )
    return {
        "message": "User registered successfully. Please check your email to verify your account.",
        "email": user.email
    }

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):

    result = verify_email_token(db, token)

    return {"message": result["message"], "email": result["user"].email}


@router.post("/login")
def login(response: Response ,form_data: OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):


    result = login_user(db, form_data.username, form_data.password)

    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=result["refresh_token"],
        httponly=True,  # ← JS cannot access
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=7 * 24 * 60 * 60  # 7 days in seconds
    )
    return {"access_token": result.get("access_token"), "token_type": "bearer"}



@router.post("/refresh")
def refresh(response: Response, refresh_token:str = Cookie(default=None), db: Session = Depends(get_db)):
    # protected by refresh token validity inside refresh_access_token()

    if refresh_token is None:
        raise HTTPException(status_code=401, detail="No refresh token")

    result = renew_access_token(db, refresh_token)
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")

    response.set_cookie(
        key=settings.refresh_cookie_name,
        value= refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=7 * 24 * 60 * 60
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(response:Response ,refresh_token:str = Cookie(default=None),

    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if refresh_token:
        payload = decode_refresh_token(refresh_token)

        if payload is not None:
            user_id = payload.get("sub")

            if user_id is not None:
                token_rows = get_active_refresh_tokens_for_user(db, int(user_id))

                for token_row in token_rows:
                    if verify_password(refresh_token, token_row.token):
                        revoke_refresh_token(db, token_row)
                        break

    response.delete_cookie(settings.refresh_cookie_name)
    return {"message": "Logged out successfully"}


@router.post("/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    """Resend verification email to user"""

    user = get_user_by_email(db, email)

    if not user:
        # Don't reveal whether email exists (security best practice)
        return {
            "message": "If an account with that email exists and is unverified, a verification email has been sent."
        }

    if user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email already verified. You can log in."
        )

    # Create new verification token
    token = create_email_verification_token(user.id)
    save_verification_token_to_db(db, user.id, token)

    # Send verification email
    verification_link = f"{settings.backend_url}/auth/verify-email?token={token}"

    body = f"""
    <html>
        <body>
            <h2>Email Verification</h2>
            <p>You requested a new verification link. Click below to verify your email:</p>
            <a href="{verification_link}">Verify Email</a>
            <p style="margin-top: 20px; color: #999;">This link expires in 24 hours.</p>
        </body>
    </html>
    """

    send_email(
        to_email=user.email,
        subject="Verify your email address",
        body=body
    )

    return {
        "message": "If an account with that email exists and is unverified, a verification email has been sent."
    }
