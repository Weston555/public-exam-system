from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.security import get_password_hash, create_access_token

router = APIRouter()


@router.post("/register")
async def register(
    username: str,
    password: str,
    role: str = "STUDENT",
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 这里应该实现用户注册逻辑
    # 暂时返回成功响应
    return {"message": "注册成功", "user_id": 1}


@router.post("/login")
async def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 这里应该实现用户登录逻辑
    # 暂时模拟登录成功

    # 模拟用户数据
    user_data = {
        "id": 1,
        "username": username,
        "role": "ADMIN" if username == "admin" else "STUDENT"
    }

    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": str(user_data["id"]), "username": username, "role": user_data["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user_data["role"],
        "expires_in": 1800
    }
