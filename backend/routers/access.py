from fastapi import APIRouter, Depends

from auth import require_app_password

router = APIRouter(dependencies=[Depends(require_app_password)])


@router.get("/check")
def check_access():
    return {"authenticated": True}
