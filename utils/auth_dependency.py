from fastapi import HTTPException, status

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.dependencies import get_db
from repository.user_repository import get_user_by_id
from utils.token import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# It does **not** create the route. It does **not** protect anything.
# It's a pointer — it tells tools *"if you need a token, go ask this URL for one."*
# The primary consumer of this information is **FastAPI's auto-generated Swagger docs** at `/docs`:

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )

    raw_user_id = payload.get("sub")
    if raw_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )

    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )

    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user





