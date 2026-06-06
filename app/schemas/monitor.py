# -*- coding: utf-8 -*-
"""监控相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MonitorOverview(BaseModel):
    """监控总览"""
    exam_id: int
    exam_name: str
    total_students: int = 0
    submitted_count: int = 0
    in_progress_count: int = 0
    not_started_count: int = 0
    abnormal_count: int = 0
    avg_score: Optional[float] = None
    pass_rate: Optional[float] = None


class MonitorStudent(BaseModel):
    """监控中的考生信息"""
    session_id: int
    user_id: int
    username: str
    name: str
    class_name: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    answered_count: int = 0
    total_questions: int = 0
    tab_switch_count: int = 0
    progress: float = 0
    last_active: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AbnormalEvent(BaseModel):
    """异常事件"""
    id: int
    session_id: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_name: Optional[str] = None
    event_type: str
    event_time: Optional[datetime] = None
    detail: Optional[str] = None

    model_config = {"from_attributes": True}


class ForceSubmitRequest(BaseModel):
    """强制交卷请求"""
    reason: str = Field(default="管理员强制交卷", description="强制交卷原因")


class TabSwitchReport(BaseModel):
    """切屏上报"""
    session_id: int = Field(..., description="会话ID")


class ExtraTimeRequest(BaseModel):
    """补时请求"""
    extra_minutes: int = Field(..., gt=0, description="额外时间(分钟),必须大于0")
