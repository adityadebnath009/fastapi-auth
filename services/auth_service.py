from datetime import datetime, timezone

from fastapi import HTTPException, status


from repository.user_repository import create_user, get_user_by_email, save_refresh_token, get_refresh_token, \
    revoke_refresh_token
from utils.hashing import hash_password, verify_password
from utils.token import create_access_token, create_refresh_token, decode_token


def register_user(db,email,password):
    existing_user = get_user_by_email(db, email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User Already Exists"
        )

    hashed = hash_password(password)

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

    access_token = create_access_token({"sub":str(user.id)})
    refresh_token = create_refresh_token({"sub" : str(user.id)})

    #
    save_refresh_token(db, user.id, refresh_token)

    return {
        "access_token" : access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



def renew_access_token(db, refresh_token: str):
    playload = decode_token(refresh_token)



    if playload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")



    db_refresh_token = get_refresh_token(db, refresh_token)

    if db_refresh_token.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked or reused")

    if  db_refresh_token is None or db_refresh_token.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    if db_refresh_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")


    user_id = playload.get("sub")

    revoke_refresh_token(db, refresh_token)



    new_access_token = create_access_token({"sub": str(user_id)})
    new_refresh_token = create_refresh_token({"sub": str(user_id)})

    save_refresh_token(db, user_id, new_refresh_token)

    return {"access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"}






