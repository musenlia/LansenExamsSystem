# -*- coding: utf-8 -*-
"""考试会话相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SessionEnterResponse(BaseModel):
    """进入考试响应"""
    session_id: int = Field(..., description="会话ID")
    exam_name: str = Field(..., description="考试名称")
    duration: int = Field(..., description="考试时长(分钟)")
    total_score: int = Field(..., description="总分")
    start_time: Optional[datetime] = Field(None, description="考试开始时间")
    status: str = Field(..., description="会话状态")


class SessionQuestionOption(BaseModel):
    """选项（可能乱序）"""
    key: str = Field(..., description="选项键")
    value: str = Field(..., description="选项值")


class SessionQuestionResponse(BaseModel):
    """考试题目（考生视角，不含正确答案）"""
    order_num: int = Field(..., description="题号")
    question_id: int = Field(..., description="题目ID")
    type: str = Field(..., description="题型")
    content: str = Field(..., description="题目内容")
    options: Optional[List[SessionQuestionOption]] = Field(None, description="选项列表(可能乱序)")
    score: int = Field(..., description="该题分值")
    difficulty: Optional[str] = Field(None, description="难度")
    fill_match_mode: Optional[str] = Field(None, description="填空匹配模式")


class SessionQuestionsResponse(BaseModel):
    """考试题目列表响应"""
    session_id: int
    exam_name: str
    duration: int
    start_time: Optional[datetime] = None
    remaining_seconds: Optional[int] = None
    total_questions: int = 0
    questions: List[SessionQuestionResponse] = []


class SubmitRequest(BaseModel):
    """提交答卷请求"""
    auto_submit: bool = Field(default=False, description="是否自动提交")


class SubmitResponse(BaseModel):
    """提交答卷响应（含成绩数据）"""
    session_id: int = Field(..., description="会话ID")
    total_score: Optional[float] = Field(None, description="得分")
    pass_score: float = Field(..., description="及格线")
    is_passed: Optional[bool] = Field(None, description="是否及格")
    time_used: Optional[int] = Field(None, description="用时(秒)")
    status: str = Field(..., description="会话状态")
