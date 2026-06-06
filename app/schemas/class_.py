# -*- coding: utf-8 -*-
"""班级相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ClassCreate(BaseModel):
    """创建班级"""
    name: str = Field(..., min_length=1, max_length=100, description="班级名称")
    description: Optional[str] = Field(None, description="班级描述")


class ClassUpdate(BaseModel):
    """更新班级"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="班级名称")
    description: Optional[str] = Field(None, description="班级描述")


class ClassResponse(BaseModel):
    """班级响应"""
    id: int
    name: str
    description: Optional[str] = None
    student_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClassDetailResponse(BaseModel):
    """班级详情响应（含学生列表）"""
    id: int
    name: str
    description: Optional[str] = None
    student_count: int = 0
    students: list = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
