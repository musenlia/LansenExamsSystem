# -*- coding: utf-8 -*-
"""JWT 生成/验证、密码工具、get_current_user 依赖"""

import bcrypt
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models.user import User

# 加载配置
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _load_jwt_config() -> dict:
    """加载 JWT 配置"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["jwt"]


_jwt_config = _load_jwt_config()
SECRET_KEY: str = _jwt_config["secret_key"]
ALGORITHM: str = _jwt_config["algorithm"]
EXPIRE_MINUTES: int = _jwt_config["expire_minutes"]

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    生成 JWT Token

    Args:
        data: 载荷数据，包含 user_id, username, role
        expires_delta: 自定义过期时间

    Returns:
        JWT Token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码并验证 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        载荷字典，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def is_bcrypt_hash(password: str) -> bool:
    """
    判断密码是否为 bcrypt 哈希格式

    Args:
        password: 待判断的密码字符串

    Returns:
        是否为 bcrypt 哈希（以 $2b$ 或 $2a$ 开头）
    """
    return password.startswith(("$2b$", "$2a$"))


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    验证密码（支持 bcrypt 哈希和明文兼容）

    优先使用 bcrypt 验证；若存储密码不是 bcrypt 格式，则回退到明文比对

    Args:
        plain_password: 用户输入的明文密码
        stored_password: 数据库存储的密码

    Returns:
        是否匹配
    """
    if is_bcrypt_hash(stored_password):
        return bcrypt.checkpw(plain_password.encode("utf-8"), stored_password.encode("utf-8"))
    return plain_password == stored_password


def get_password_hash(password: str) -> str:
    """
    使用 bcrypt 加密密码

    Args:
        password: 原始明文密码

    Returns:
        bcrypt 哈希后的密码字符串
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI 依赖注入：获取当前登录用户

    Raises:
        HTTPException: 未认证或 Token 无效
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """可选认证 - 未登录返回 None 而非抛异常"""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员角色"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


async def require_admin_or_teacher(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员或教师角色"""
    if current_user.role not in ("admin", "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员或教师权限",
        )
    return current_user


async def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    """要求教师角色"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限",
        )
    return current_user
