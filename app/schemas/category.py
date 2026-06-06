# -*- coding: utf-8 -*-
"""分类相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """创建分类"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    description: Optional[str] = Field(None, description="分类描述")
    sort_order: int = Field(default=0, description="排序序号")


class CategoryUpdate(BaseModel):
    """更新分类"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="分类名称")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    description: Optional[str] = Field(None, description="分类描述")
    sort_order: Optional[int] = Field(None, description="排序序号")


class CategoryResponse(BaseModel):
    """分类响应"""
    id: int
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0
    question_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CategoryTreeResponse(BaseModel):
    """分类树形响应（含子分类）"""
    id: int
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0
    question_count: int = 0
    children: List["CategoryTreeResponse"] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
