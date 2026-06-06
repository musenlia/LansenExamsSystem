# -*- coding: utf-8 -*-
"""系统管理相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ConfigUpdate(BaseModel):
    """系统配置更新（单条）"""
    config_key: str = Field(..., description="配置键")
    config_value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")


class ConfigBatchUpdate(BaseModel):
    """系统配置批量更新"""
    configs: List[Dict[str, str]] = Field(..., description="配置列表，每项含 key 和 value")


class ConfigResponse(BaseModel):
    """系统配置响应"""
    id: int
    config_key: str
    config_value: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OperationLogResponse(BaseModel):
    """操作日志响应"""
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    """仪表盘数据"""
    total_users: int = 0
    total_students: int = 0
    total_classes: int = 0
    total_questions: int = 0
    total_exams: int = 0
    ongoing_exams: int = 0
    recent_exams: List[dict] = []
    exam_stats: Dict[str, Any] = {}

    model_config = {"from_attributes": True}
