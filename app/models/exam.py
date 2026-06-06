# -*- coding: utf-8 -*-
"""Exam 考试模型 + ExamQuestion 考试题目关联 + ExamClass 考试班级关联"""

from datetime import datetime
from sqlalchemy import (
    Integer, String, DateTime, Text, JSON, Boolean, Enum as SAEnum,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Exam(Base):
    """考试表"""

    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="考试ID")
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="考试名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="考试描述")
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="开始时间")
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=60, comment="考试时长(分钟)")
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100, comment="总分")
    pass_score: Mapped[int] = mapped_column(Integer, nullable=False, default=60, comment="及格分")
    mode: Mapped[str] = mapped_column(
        SAEnum("fixed", "random", name="exam_mode"),
        nullable=False,
        default="fixed",
        comment="组卷模式: fixed-固定, random-随机",
    )
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "published", "ongoing", "paused", "ended", "archived", name="exam_status"),
        nullable=False,
        default="draft",
        comment="状态: draft-草稿, published-已发布, ongoing-进行中, paused-已暂停, ended-已结束, archived-已归档",
    )
    shuffle_question: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否乱序题目"
    )
    shuffle_option: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否乱序选项"
    )
    allow_early_submit: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否允许提前交卷"
    )
    random_config: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="随机组卷配置(JSON)")
    notice: Mapped[str | None] = mapped_column(Text, nullable=True, comment="考试注意事项")
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, comment="创建人ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    exam_questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    exam_classes = relationship("ExamClass", back_populates="exam", cascade="all, delete-orphan")
    sessions = relationship("ExamSession", back_populates="exam", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Exam(id={self.id}, name='{self.name}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration": self.duration,
            "total_score": self.total_score,
            "pass_score": self.pass_score,
            "mode": self.mode,
            "status": self.status,
            "shuffle_question": self.shuffle_question,
            "shuffle_option": self.shuffle_option,
            "allow_early_submit": self.allow_early_submit,
            "random_config": self.random_config,
            "notice": self.notice,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ExamQuestion(Base):
    """考试-题目关联表"""

    __tablename__ = "exam_questions"
    __table_args__ = (
        UniqueConstraint("exam_id", "question_id", name="uq_exam_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="关联ID")
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False, comment="考试ID"
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False, comment="题目ID"
    )
    order_num: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="题目排序号")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=2, comment="该题分值")

    # 关系
    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question", back_populates="exam_questions")

    def __repr__(self) -> str:
        return f"<ExamQuestion(exam_id={self.exam_id}, question_id={self.question_id}, order={self.order_num})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "question_id": self.question_id,
            "order_num": self.order_num,
            "score": self.score,
        }


class ExamClass(Base):
    """考试-班级关联表"""

    __tablename__ = "exam_classes"
    __table_args__ = (
        UniqueConstraint("exam_id", "class_id", name="uq_exam_class"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="关联ID")
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False, comment="考试ID"
    )
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False, comment="班级ID"
    )

    # 关系
    exam = relationship("Exam", back_populates="exam_classes")
    class_ = relationship("Class", back_populates="exam_classes")

    def __repr__(self) -> str:
        return f"<ExamClass(exam_id={self.exam_id}, class_id={self.class_id})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "class_id": self.class_id,
        }
