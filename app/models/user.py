# -*- coding: utf-8 -*-
"""User 用户模型"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(Base):
    """用户表 - 管理员和考生"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="登录用户名")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="真实姓名")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="登录密码(明文)")
    role: Mapped[str] = mapped_column(
        SAEnum("admin", "teacher", "student", name="user_role"),
        nullable=False,
        default="student",
        comment="角色: admin-管理员, teacher-教师, student-考生",
    )
    class_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True, comment="所属班级ID"
    )
    status: Mapped[str] = mapped_column(
        SAEnum("active", "disabled", name="user_status"),
        nullable=False,
        default="active",
        comment="状态: active-启用, disabled-禁用",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 关系
    class_obj = relationship("Class", foreign_keys=[class_id], lazy="select")
    exam_sessions = relationship("ExamSession", back_populates="user", lazy="dynamic")
    operation_logs = relationship("OperationLog", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "role": self.role,
            "class_id": self.class_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
