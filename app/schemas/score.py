# -*- coding: utf-8 -*-
"""成绩相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ScoreListResponse(BaseModel):
    """成绩列表项"""
    session_id: int
    user_id: int
    username: str
    name: str
    class_name: Optional[str] = None
    total_score: Optional[int] = None
    status: str
    time_used: Optional[int] = None
    submit_time: Optional[datetime] = None
    start_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ScoreDetailResponse(BaseModel):
    """答卷详情"""
    session_id: int
    exam_id: int
    exam_name: str
    user_id: int
    username: str
    name: str
    total_score: Optional[int] = None
    status: str
    start_time: Optional[datetime] = None
    submit_time: Optional[datetime] = None
    time_used: Optional[int] = None
    answers: List[dict] = []

    model_config = {"from_attributes": True}


class ScoreStatsResponse(BaseModel):
    """成绩统计"""
    exam_id: int
    exam_name: str
    total_students: int = 0
    submitted_count: int = 0
    avg_score: Optional[float] = None
    max_score: Optional[int] = None
    min_score: Optional[int] = None
    pass_count: int = 0
    pass_rate: Optional[float] = None
    score_distribution: List[dict] = []

    model_config = {"from_attributes": True}
