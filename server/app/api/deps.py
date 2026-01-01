from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_token_payload

# JWT Bearer 认证
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    token = credentials.credentials
    payload = get_token_payload(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户令牌",
        )

    # 这里应该从数据库查询用户，但现在先返回基本信息
    return {
        "id": int(user_id),
        "username": payload.get("username"),
        "role": payload.get("role")
    }


def get_current_student(current_user: dict = Depends(get_current_user)):
    """获取当前学员用户（需要STUDENT角色）"""
    if current_user["role"] != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要学员权限",
        )
    return current_user


def get_current_admin(current_user: dict = Depends(get_current_user)):
    """获取当前管理员用户（需要ADMIN角色）"""
    if current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
