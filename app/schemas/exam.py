# -*- coding: utf-8 -*-
"""考试相关 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExamQuestionSet(BaseModel):
    """考试题目设置项"""
    question_id: int = Field(..., description="题目ID")
    score: int = Field(default=2, description="该题分值")
    order_num: int = Field(default=0, description="排序号")


class TypeRuleConfig(BaseModel):
    """题型抽取规则"""
    type: str = Field(..., description="题型: single/multiple/judge/fill")
    count: int = Field(default=0, description="抽取数量")
    score_per_question: int = Field(default=2, description="每题分值")
    category_id: Optional[int] = Field(None, description="限定分类ID（可选）")
    difficulty: Optional[str] = Field(None, description="限定难度（可选）")


class RandomConfig(BaseModel):
    """随机组卷配置"""
    category_id: Optional[int] = None
    difficulty: Optional[str] = None
    count: int = Field(default=10, description="随机抽取数量")
    score_per_question: int = Field(default=2, description="每题分值")
    type_rules: Optional[List[TypeRuleConfig]] = Field(None, description="按题型抽取规则（优先级高于通用配置）")


class ExamCreate(BaseModel):
    """创建考试"""
    name: str = Field(..., min_length=1, max_length=200, description="考试名称")
    description: Optional[str] = Field(None, description="考试描述")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    duration: int = Field(default=60, description="考试时长(分钟)")
    total_score: int = Field(default=100, description="总分")
    pass_score: int = Field(default=60, description="及格分")
    mode: str = Field(default="fixed", description="组卷模式: fixed/random")
    shuffle_question: bool = Field(default=False, description="是否乱序题目")
    shuffle_option: bool = Field(default=False, description="是否乱序选项")
    allow_early_submit: bool = Field(default=True, description="是否允许提前交卷")
    random_config: Optional[Dict[str, Any]] = Field(None, description="随机组卷配置")
    notice: Optional[str] = Field(None, description="考试注意事项")
    class_ids: List[int] = Field(default_factory=list, description="参考班级ID列表")
    questions: List[ExamQuestionSet] = Field(default_factory=list, description="题目列表(fixed模式)")


class ExamUpdate(BaseModel):
    """更新考试"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="考试名称")
    description: Optional[str] = Field(None, description="考试描述")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    duration: Optional[int] = Field(None, description="考试时长(分钟)")
    total_score: Optional[int] = Field(None, description="总分")
    pass_score: Optional[int] = Field(None, description="及格分")
    mode: Optional[str] = Field(None, description="组卷模式")
    shuffle_question: Optional[bool] = Field(None, description="是否乱序题目")
    shuffle_option: Optional[bool] = Field(None, description="是否乱序选项")
    allow_early_submit: Optional[bool] = Field(None, description="是否允许提前交卷")
    random_config: Optional[Dict[str, Any]] = Field(None, description="随机组卷配置")
    notice: Optional[str] = Field(None, description="考试注意事项")
    class_ids: Optional[List[int]] = Field(None, description="参考班级ID列表")
    questions: Optional[List[ExamQuestionSet]] = Field(None, description="题目列表")


class ExamResponse(BaseModel):
    """考试响应"""
    id: int
    name: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: int = 60
    total_score: int = 100
    pass_score: int = 60
    mode: str = "fixed"
    status: str = "draft"
    shuffle_question: bool = False
    shuffle_option: bool = False
    allow_early_submit: bool = True
    random_config: Optional[Dict[str, Any]] = None
    notice: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class_names: Optional[List[str]] = None
    class_ids: Optional[List[int]] = None
    question_count: int = 0

    model_config = {"from_attributes": True}


class ExamDetailResponse(BaseModel):
    """考试详情响应（含题目列表和班级列表）"""
    id: int
    name: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    duration: int = 60
    total_score: int = 100
    pass_score: int = 60
    mode: str = "fixed"
    status: str = "draft"
    shuffle_question: bool = False
    shuffle_option: bool = False
    allow_early_submit: bool = True
    random_config: Optional[Dict[str, Any]] = None
    notice: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    classes: List[dict] = []
    questions: List[dict] = []

    model_config = {"from_attributes": True}
