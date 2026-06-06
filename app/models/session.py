# -*- coding: utf-8 -*-
"""ExamSession 考试会话模型"""

from datetime import datetime
from sqlalchemy import (
    Integer, String, DateTime, JSON, Boolean, Enum as SAEnum,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class ExamSession(Base):
    """考试会话表 - 每个考生对每场考试有且仅有一条记录"""

    __tablename__ = "exam_sessions"
    __table_args__ = (
        UniqueConstraint("exam_id", "user_id", name="uq_exam_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="会话ID")
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False, comment="考试ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, comment="考生ID"
    )
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="开始答题时间")
    submit_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="提交时间")
    time_used: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="用时(秒)")
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="得分")
    status: Mapped[str] = mapped_column(
        SAEnum(
            "not_started", "in_progress", "submitted",
            "force_submitted", "auto_submitted",
            name="session_status",
        ),
        nullable=False,
        default="not_started",
        comment="状态: not_started-未开始, in_progress-答题中, submitted-已提交, force_submitted-强制提交, auto_submitted-自动提交",
    )
    question_order: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="题目乱序(JSON数组)")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否活跃"
    )
    extra_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0, comment="额外增加的时间(秒)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )

    # 关系
    exam = relationship("Exam", back_populates="sessions")
    user = relationship("User", back_populates="exam_sessions")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")
    monitor_logs = relationship("MonitorLog", back_populates="session", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<ExamSession(id={self.id}, exam_id={self.exam_id}, user_id={self.user_id}, status='{self.status}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "submit_time": self.submit_time.isoformat() if self.submit_time else None,
            "time_used": self.time_used,
            "total_score": self.total_score,
            "status": self.status,
            "question_order": self.question_order,
            "is_active": self.is_active,
            "extra_time": self.extra_time or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
