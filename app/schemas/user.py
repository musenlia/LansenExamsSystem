# -*- coding: utf-8 -*-
"""用户相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(..., min_length=2, max_length=50, description="登录用户名")
    name: str = Field(..., min_length=1, max_length=100, description="真实姓名")
    password: str = Field(..., min_length=1, max_length=255, description="登录密码")
    role: str = Field(default="student", description="角色: admin/teacher/student")
    class_id: Optional[int] = Field(None, description="所属班级ID")
    status: str = Field(default="active", description="状态: active/disabled")


class UserUpdate(BaseModel):
    """更新用户"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="真实姓名")
    password: Optional[str] = Field(None, min_length=1, max_length=255, description="登录密码")
    role: Optional[str] = Field(None, description="角色: admin/student")
    class_id: Optional[int] = Field(None, description="所属班级ID")
    status: Optional[str] = Field(None, description="状态: active/disabled")


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    name: str
    role: str
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """用户列表项"""
    id: int
    username: str
    name: str
    role: str
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PasswordChange(BaseModel):
    """修改密码"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=1, max_length=255, description="新密码")


class PasswordReset(BaseModel):
    """重置密码"""
    new_password: str = Field(default="123456", description="新密码")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: UserResponse
