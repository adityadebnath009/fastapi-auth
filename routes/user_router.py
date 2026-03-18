from fastapi import APIRouter, Depends

from schemas.user_schemas import UserResponse
from utils.auth_dependency import get_current_user

router  = APIRouter(prefix="/users", tags = ["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user