# -*- coding: utf-8 -*-
"""Question 题目模型"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, JSON, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Question(Base):
    """题目表"""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="题目ID")
    type: Mapped[str] = mapped_column(
        SAEnum("single", "multiple", "judge", "fill", name="question_type"),
        nullable=False,
        comment="题型: single-单选, multiple-多选, judge-判断, fill-填空",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="题目内容")
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="选项(JSON格式)")
    answer: Mapped[str] = mapped_column(Text, nullable=False, comment="正确答案")
    fill_match_mode: Mapped[str | None] = mapped_column(
        SAEnum("exact", "contain", name="fill_match_mode"),
        nullable=True,
        comment="填空匹配模式: exact-精确, contain-包含",
    )
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True, comment="题目解析")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=2, comment="分值")
    difficulty: Mapped[str] = mapped_column(
        SAEnum("easy", "medium", "hard", name="question_difficulty"),
        nullable=False,
        default="medium",
        comment="难度: easy-简单, medium-中等, hard-困难",
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True, comment="所属分类ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关系
    category = relationship("Category", back_populates="questions")
    exam_questions = relationship("ExamQuestion", back_populates="question", lazy="dynamic")
    answers = relationship("Answer", back_populates="question", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, type='{self.type}', content='{self.content[:20]}...')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "options": self.options,
            "answer": self.answer,
            "fill_match_mode": self.fill_match_mode,
            "analysis": self.analysis,
            "score": self.score,
            "difficulty": self.difficulty,
            "category_id": self.category_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
