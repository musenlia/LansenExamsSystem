# -*- coding: utf-8 -*-
"""SystemConfig 系统配置模型"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class SystemConfig(Base):
    """系统配置表 - 键值对存储"""

    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="配置ID")
    config_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="配置键"
    )
    config_value: Mapped[str] = mapped_column(Text, nullable=False, comment="配置值")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="配置描述")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<SystemConfig(key='{self.config_key}', value='{self.config_value}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
