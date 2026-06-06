# -*- coding: utf-8 -*-
"""OperationLog 操作日志模型"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class OperationLog(Base):
    """操作日志表 - 记录管理员的操作行为"""

    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="日志ID")
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, comment="操作用户ID"
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, comment="操作动作")
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="操作对象类型")
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作对象ID")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="操作详情")
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="IP地址")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )

    # 关系
    user = relationship("User", back_populates="operation_logs")

    def __repr__(self) -> str:
        return f"<OperationLog(id={self.id}, action='{self.action}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "detail": self.detail,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
