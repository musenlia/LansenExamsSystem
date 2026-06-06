# -*- coding: utf-8 -*-
"""Answer 答题记录模型"""

from datetime import datetime
from sqlalchemy import (
    Integer, String, DateTime, Text, JSON, Boolean,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Answer(Base):
    """答题记录表 - 每道题一条记录"""

    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_session_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="答题ID")
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_sessions.id", ondelete="CASCADE"),
        nullable=False, comment="会话ID"
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False, comment="题目ID"
    )
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True, comment="考生答案")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="得分")
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="是否正确")
    option_order: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="选项乱序(JSON数组)")
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="答题时间")
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否标记")

    # 关系
    session = relationship("ExamSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def __repr__(self) -> str:
        return f"<Answer(id={self.id}, session_id={self.session_id}, question_id={self.question_id})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "question_id": self.question_id,
            "user_answer": self.user_answer,
            "score": self.score,
            "is_correct": self.is_correct,
            "option_order": self.option_order,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
            "is_flagged": self.is_flagged if self.is_flagged is not None else False,
        }
