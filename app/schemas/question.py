# -*- coding: utf-8 -*-
"""题目相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class QuestionOptionItem(BaseModel):
    """题目选项"""
    label: str = Field(..., description="选项标签: A/B/C/D 或 true/false")
    content: str = Field(..., description="选项内容")
    is_correct: bool = Field(default=False, description="是否正确答案")


class QuestionCreate(BaseModel):
    """创建题目"""
    type: str = Field(..., description="题型: single/multiple/judge/fill")
    content: str = Field(..., description="题目内容")
    options: Optional[list] = Field(None, description="选项列表")
    answer: str = Field(..., description="正确答案")
    fill_match_mode: Optional[str] = Field(None, description="填空匹配模式: exact/contain")
    analysis: Optional[str] = Field(None, description="题目解析")
    score: int = Field(default=2, description="分值")
    difficulty: str = Field(default="medium", description="难度: easy/medium/hard")
    category_id: Optional[int] = Field(None, description="所属分类ID")


class QuestionUpdate(BaseModel):
    """更新题目"""
    type: Optional[str] = Field(None, description="题型")
    content: Optional[str] = Field(None, description="题目内容")
    options: Optional[list] = Field(None, description="选项列表")
    answer: Optional[str] = Field(None, description="正确答案")
    fill_match_mode: Optional[str] = Field(None, description="填空匹配模式")
    analysis: Optional[str] = Field(None, description="题目解析")
    score: Optional[int] = Field(None, description="分值")
    difficulty: Optional[str] = Field(None, description="难度")
    category_id: Optional[int] = Field(None, description="所属分类ID")


class QuestionResponse(BaseModel):
    """题目响应"""
    id: int
    type: str
    content: str
    options: Optional[list] = None
    answer: str
    fill_match_mode: Optional[str] = None
    analysis: Optional[str] = None
    score: int
    difficulty: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class QuestionStatsResponse(BaseModel):
    """题目统计响应"""
    total: int = 0
    single_count: int = 0
    multiple_count: int = 0
    judge_count: int = 0
    fill_count: int = 0
    easy_count: int = 0
    medium_count: int = 0
    hard_count: int = 0

    model_config = {"from_attributes": True}
