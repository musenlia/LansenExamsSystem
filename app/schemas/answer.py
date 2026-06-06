# -*- coding: utf-8 -*-
"""答题相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AnswerSaveRequest(BaseModel):
    """保存答案请求"""
    question_id: int = Field(..., description="题目ID")
    user_answer: str = Field(..., description="考生答案")


class AnswerResponse(BaseModel):
    """答题记录响应"""
    id: int
    session_id: int
    question_id: int
    user_answer: Optional[str] = None
    score: Optional[int] = None
    is_correct: Optional[bool] = None
    answered_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AnswerDetailResponse(BaseModel):
    """答题详情响应（含题目信息和正确答案）"""
    id: int
    question_id: int
    type: str
    content: str
    options: Optional[Dict[str, Any]] = None
    user_answer: Optional[str] = None
    correct_answer: str = ""
    score: Optional[int] = None
    max_score: int = 0
    is_correct: Optional[bool] = None
    analysis: Optional[str] = None

    model_config = {"from_attributes": True}
