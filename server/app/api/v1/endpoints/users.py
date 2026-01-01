from fastapi import APIRouter, Depends

from ..deps import get_current_user

router = APIRouter()


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user
