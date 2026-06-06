# -*- coding: utf-8 -*-
"""认证服务 - JWT 生成/验证、登录认证、Token 刷新"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from models.user import User
from utils.security import (
    create_access_token,
    decode_access_token,
    verify_password,
    get_password_hash,
)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    用户认证（明文密码比对）

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        认证成功返回 User 对象，失败返回 None
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    if user.status != "active":
        return None
    return user


def login(db: Session, username: str, password: str) -> Tuple[Optional[str], Optional[User], str]:
    """
    登录

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        (token, user, message)
    """
    user = authenticate_user(db, username, password)
    if user is None:
        return None, None, "用户名或密码错误"

    # 更新最后登录时间
    user.updated_at = datetime.now()
    db.commit()

    # 生成 JWT
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }
    token = create_access_token(token_data)

    return token, user, "登录成功"


def refresh_token(db: Session, user_id: int) -> Tuple[Optional[str], str]:
    """
    刷新 Token（答题期间延长有效期）

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        (new_token, message)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None, "用户不存在"

    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }
    # 刷新时延长到 2 小时
    token = create_access_token(token_data, expires_delta=timedelta(hours=2))

    return token, "Token 刷新成功"


def change_password(db: Session, user: User, old_password: str, new_password: str) -> Tuple[bool, str]:
    """
    修改密码

    Args:
        db: 数据库会话
        user: 当前用户
        old_password: 旧密码
        new_password: 新密码

    Returns:
        (success, message)
    """
    if not verify_password(old_password, user.password):
        return False, "旧密码错误"

    user.password = get_password_hash(new_password)
    user.updated_at = datetime.now()
    db.commit()
    return True, "密码修改成功"


def reset_password(db: Session, user_id: int, new_password: str = "123456") -> Tuple[bool, str]:
    """
    重置密码

    Args:
        db: 数据库会话
        user_id: 目标用户ID
        new_password: 新密码

    Returns:
        (success, message)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False, "用户不存在"

    user.password = get_password_hash(new_password)
    user.updated_at = datetime.now()
    db.commit()
    return True, f"密码已重置为: {new_password}"
