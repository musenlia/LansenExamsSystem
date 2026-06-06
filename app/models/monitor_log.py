# -*- coding: utf-8 -*-
"""MonitorLog 监控日志模型"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class MonitorLog(Base):
    """监控日志表 - 记录考试过程中的异常事件"""

    __tablename__ = "monitor_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="日志ID")
    session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("exam_sessions.id", ondelete="SET NULL"),
        nullable=True, comment="会话ID"
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, comment="用户ID"
    )
    exam_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="SET NULL"),
        nullable=True, comment="考试ID"
    )
    event_type: Mapped[str] = mapped_column(
        SAEnum(
            "tab_switch", "multi_login", "auto_submit",
            "force_submit", "login", "logout",
            name="monitor_event_type",
        ),
        nullable=False,
        comment="事件类型: tab_switch-切屏, multi_login-多端登录, auto_submit-自动提交, force_submit-强制提交, login-登录, logout-退出",
    )
    event_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="事件时间"
    )
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="事件详情")

    # 关系
    session = relationship("ExamSession", back_populates="monitor_logs")

    def __repr__(self) -> str:
        return f"<MonitorLog(id={self.id}, event_type='{self.event_type}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "exam_id": self.exam_id,
            "event_type": self.event_type,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "detail": self.detail,
        }
