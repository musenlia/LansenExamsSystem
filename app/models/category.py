# -*- coding: utf-8 -*-
"""Category 题目分类模型"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Category(Base):
    """题目分类表 - 支持自引用父子关系"""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="分类名称")
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True, comment="父分类ID(自引用)"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="分类描述")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序序号")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )

    # 关系
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", lazy="dynamic")
    questions = relationship("Question", back_populates="category", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "description": self.description,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
