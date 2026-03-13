from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi.params import Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database.dependencies import get_db
from repository.user_repository import revoke_refresh_token
from schemas.RefreshTokenRequest import RefreshTokenRequest
from services.auth_service import register_user, login_user, renew_access_token
from utils.auth_dependency import get_current_user

from schemas.user_schemas import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])




@router.post("/register")
def register(user: UserCreate,  db:Session = Depends(get_db)):
    return register_user(db, user.email, user.password)



@router.post("/login")
def login(response: Response ,form_data: OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):


    result = login_user(db, form_data.username, form_data.password)

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,  # ← JS cannot access
        secure=True,  # ← only sent over HTTPS
        samesite="lax",  # ← CSRF protection
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
        key="refresh_token",
        value= refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request ,response:Response ,refresh_token:str = Cookie(default=None),

    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        revoke_refresh_token(db, refresh_token)

    response.delete_cookie("refresh_token")

    return {"message": "Logged out successfully"}
