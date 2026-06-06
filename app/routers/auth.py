# -*- coding: utf-8 -*-
"""认证路由 - 登录、登出、获取当前用户、修改密码、Token刷新"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.user import LoginRequest, LoginResponse, UserResponse, PasswordChange
from services.auth_service import login as do_login, change_password
from utils.security import get_current_user, decode_access_token, create_access_token

router = APIRouter()


@router.post("/login", summary="用户登录")
def auth_login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    token, user, message = do_login(db, request.username, request.password)
    if not token:
        return {"code": 401, "data": None, "message": message}

    # 构建用户响应
    user_dict = user.to_dict()
    if user.class_id:
        from models.class_ import Class
        cls = db.query(Class).filter(Class.id == user.class_id).first()
        user_dict["class_name"] = cls.name if cls else None
    else:
        user_dict["class_name"] = None

    return {
        "code": 0,
        "data": {
            "token": token,
            "user": user_dict,
        },
        "message": "success",
    }


@router.post("/logout", summary="用户登出")
def auth_logout(current_user: User = Depends(get_current_user)):
    """用户登出（前端清除 Token 即可）"""
    return {"code": 0, "data": None, "message": "登出成功"}


@router.get("/me", summary="获取当前用户信息")
def auth_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前登录用户信息"""
    user_dict = current_user.to_dict()
    if current_user.class_id:
        from models.class_ import Class
        cls = db.query(Class).filter(Class.id == current_user.class_id).first()
        user_dict["class_name"] = cls.name if cls else None
    else:
        user_dict["class_name"] = None

    return {"code": 0, "data": user_dict, "message": "success"}


@router.put("/password", summary="修改密码")
def auth_change_password(
    request: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户密码"""
    success, message = change_password(db, current_user, request.old_password, request.new_password)
    if not success:
        return {"code": 400, "data": None, "message": message}
    return {"code": 0, "data": None, "message": message}


@router.post("/refresh", summary="刷新Token")
def refresh_token_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """刷新 JWT Token - 延长会话有效期"""
    token_data = {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }
    from datetime import timedelta
    new_token = create_access_token(token_data, expires_delta=timedelta(hours=2))

    return {
        "code": 0,
        "data": {
            "token": new_token,
        },
        "message": "Token 刷新成功",
    }
