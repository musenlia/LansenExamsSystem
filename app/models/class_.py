# -*- coding: utf-8 -*-
"""Class 班级模型"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Class(Base):
    """班级表"""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="班级ID")
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="班级名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="班级描述")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关系
    students = relationship("User", back_populates="class_obj", lazy="dynamic", foreign_keys="[User.class_id]")
    exam_classes = relationship("ExamClass", back_populates="class_", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Class(id={self.id}, name='{self.name}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
