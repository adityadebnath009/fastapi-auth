from fastapi import APIRouter, Depends

from utils.auth_dependency import get_current_user

router  = APIRouter(prefix="/users", tags = ["users"])


@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return current_user