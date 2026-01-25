from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ....core.database import get_db
from ....core.security import get_password_hash, create_access_token
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
    # 查找用户；如果不存在则自动创建（以便任意账号密码都能登录）
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        # 创建用户并持久化，角色参考请求中的 role，否则默认 STUDENT
        role_to_set = (request.role or "STUDENT").upper()
        # 为避免在 login 路径对任意密码做复杂哈希（可能在某些环境触发 bcrypt 限制），
        # 在此使用空字符串作为占位密码哈希（登录不会校验密码）
        hashed_password = ""
        db_user = User(
            username=request.username,
            password_hash=hashed_password,
            role=role_to_set
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        user = db_user
    else:
        # 如果请求带了 role，则同步更新用户角色（方便管理员端直接以 admin 登录）
        if request.role:
            user.role = request.role.upper()
            db.add(user)
            db.commit()
            db.refresh(user)

    # 注意：按照需求，登录时接受任意密码（不再校验密码），但依然校验账号状态
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
