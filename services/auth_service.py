from datetime import datetime, timezone

from fastapi import HTTPException, status


from repository.user_repository import create_user, get_user_by_email, save_refresh_token, get_refresh_token, \
    revoke_refresh_token, get_active_refresh_tokens_for_user
from utils.hashing import hash_password, verify_password
from utils.token import create_access_token, create_refresh_token, decode_token, decode_refresh_token


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



