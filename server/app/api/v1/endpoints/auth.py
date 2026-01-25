from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ....core.database import get_db
from ....core.security import get_password_hash, create_access_token, verify_password
from ....core.config import settings
from ....models.user import User

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "STUDENT"


class LoginRequest(BaseModel):
    username: str
    password: str
    # 可选的角色字段：前端可在登录时指定希望以哪个角色登录（'STUDENT' 或 'ADMIN'）
    role: Optional[str] = None


@router.post("/register")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 创建新用户
    hashed_password = get_password_hash(request.password)
    db_user = User(
        username=request.username,
        password_hash=hashed_password,
        role=request.role.upper()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "注册成功", "user_id": db_user.id}


@router.post("/login")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == request.username).first()

    if settings.allow_any_login:
        # 允许任意账号密码登录（演示/本地调试模式）
        if not user:
            # 自动创建用户并设置为请求角色或默认 STUDENT
            role_to_set = (request.role or "STUDENT").upper()
            db_user = User(
                username=request.username,
                password_hash="",  # 占位，不用于验证
                role=role_to_set
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            user = db_user
        else:
            if request.role:
                user.role = request.role.upper()
                db.add(user)
                db.commit()
                db.refresh(user)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用"
            )
    else:
        # 正常认证流程：必须存在且密码验证通过
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        if not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用"
            )

    # 创建访问令牌并返回（保持原有返回结构）
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.lower(),
        "expires_in": 1800
    }
