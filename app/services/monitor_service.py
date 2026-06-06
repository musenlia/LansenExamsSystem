# -*- coding: utf-8 -*-
"""监控服务 - 监控总览、考生进度、异常记录、强制交卷、WebSocket推送"""

import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from fastapi import WebSocket
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.session import ExamSession
from models.exam import Exam, ExamQuestion, ExamClass
from models.answer import Answer
from models.question import Question
from models.user import User
from models.class_ import Class
from models.monitor_log import MonitorLog


# WebSocket 连接管理器
class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # exam_id -> list of websocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, exam_id: int):
        """建立连接"""
        await websocket.accept()
        if exam_id not in self.active_connections:
            self.active_connections[exam_id] = []
        self.active_connections[exam_id].append(websocket)

    def disconnect(self, websocket: WebSocket, exam_id: int):
        """断开连接"""
        if exam_id in self.active_connections:
            if websocket in self.active_connections[exam_id]:
                self.active_connections[exam_id].remove(websocket)
            if not self.active_connections[exam_id]:
                del self.active_connections[exam_id]

    async def broadcast_to_exam(self, exam_id: int, message: dict):
        """向某场考试的所有监控者广播消息"""
        if exam_id in self.active_connections:
            dead = []
            for ws in self.active_connections[exam_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[exam_id].remove(ws)


# 全局连接管理器实例
ws_manager = ConnectionManager()


class MonitorService:
    """监控服务"""

    @staticmethod
    def get_overview(db: Session, exam_id: int) -> Optional[dict]:
        """获取监控总览"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        # 自动更新考试时间状态
        from services.session_service import SessionService
        SessionService._check_exam_time(db, exam)
        db.refresh(exam)

        # 获取该考试所有会话
        sessions = db.query(ExamSession).filter(ExamSession.exam_id == exam_id).all()
        total_students = len(sessions)
        submitted_count = sum(1 for s in sessions if s.status in ("submitted", "force_submitted", "auto_submitted"))
        in_progress_count = sum(1 for s in sessions if s.status == "in_progress")
        not_started_count = sum(1 for s in sessions if s.status == "not_started")

        # 计算未登录人数（班级总学生数 - 已创建会话数）
        not_logged_count = 0
        exam_classes = db.query(ExamClass).filter(ExamClass.exam_id == exam_id).all()
        if exam_classes:
            class_ids = [ec.class_id for ec in exam_classes]
            expected_total = db.query(func.count(User.id)).filter(
                User.class_id.in_(class_ids),
                User.role == "student",
                User.status == 1,
            ).scalar() or 0
            # 去重（同一学生可能因多班级重复计算）
            not_logged_count = max(0, expected_total - total_students)

        # 异常次数
        abnormal_count = db.query(MonitorLog).filter(
            MonitorLog.exam_id == exam_id,
            MonitorLog.event_type.in_(["tab_switch", "multi_login"]),
        ).count()

        # 平均分
        submitted_scores = [s.total_score for s in sessions if s.total_score is not None]
        avg_score = sum(submitted_scores) / len(submitted_scores) if submitted_scores else None
        pass_rate = None
        if submitted_scores:
            passed = sum(1 for sc in submitted_scores if sc >= exam.pass_score)
            pass_rate = round(passed / len(submitted_scores) * 100, 1)

        return {
            "exam_id": exam.id,
            "exam_name": exam.name,
            "status": exam.status,
            "duration": exam.duration,
            "start_time": exam.start_time.isoformat() if exam.start_time else None,
            "total_students": total_students,
            "submitted_count": submitted_count,
            "in_progress_count": in_progress_count,
            "not_started_count": not_started_count,
            "abnormal_count": abnormal_count,
            "avg_score": round(avg_score, 1) if avg_score is not None else None,
            "pass_rate": pass_rate,
            "not_logged_count": not_logged_count,
        }

    @staticmethod
    def get_students(db: Session, exam_id: int) -> List[dict]:
        """获取考生进度列表"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return []
        duration_minutes = exam.duration or 0

        sessions = db.query(ExamSession).filter(ExamSession.exam_id == exam_id).all()
        result = []

        total_questions = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).count()

        for session in sessions:
            user = db.query(User).filter(User.id == session.user_id).first()
            if not user:
                continue

            class_name = None
            if user.class_id:
                cls = db.query(Class).filter(Class.id == user.class_id).first()
                class_name = cls.name if cls else None

            # 已答题数
            answered_count = db.query(Answer).filter(
                Answer.session_id == session.id,
                Answer.user_answer.isnot(None),
                Answer.user_answer != "",
            ).count()

            # 切屏次数
            tab_switch_count = db.query(MonitorLog).filter(
                MonitorLog.session_id == session.id,
                MonitorLog.event_type == "tab_switch",
            ).count()

            # 最后活跃时间
            last_answer = db.query(Answer).filter(
                Answer.session_id == session.id,
            ).order_by(Answer.answered_at.desc()).first()
            last_active = last_answer.answered_at if last_answer else session.start_time

            progress = round(answered_count / total_questions * 100, 1) if total_questions > 0 else 0

            # 计算剩余时间（仅 in_progress 状态）
            remaining_seconds = None
            if session.status == "in_progress" and session.start_time and duration_minutes > 0:
                elapsed = (datetime.now() - session.start_time).total_seconds()
                remaining_seconds = max(0, int(duration_minutes * 60 - elapsed))

            result.append({
                "session_id": session.id,
                "user_id": user.id,
                "username": user.username,
                "name": user.name,
                "class_name": class_name,
                "status": session.status,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "answered_count": answered_count,
                "total_questions": total_questions,
                "tab_switch_count": tab_switch_count,
                "progress": progress,
                "remaining_seconds": remaining_seconds,
                "last_active": last_active.isoformat() if last_active else None,
            })

        return result

    @staticmethod
    def get_abnormal_events(db: Session, exam_id: int) -> List[dict]:
        """获取异常事件列表"""
        logs = db.query(MonitorLog).filter(
            MonitorLog.exam_id == exam_id,
            MonitorLog.event_type.in_(["tab_switch", "multi_login", "force_submit"]),
        ).order_by(MonitorLog.event_time.desc()).all()

        result = []
        for log in logs:
            log_dict = log.to_dict()
            # 附加用户信息
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if user:
                    log_dict["username"] = user.username
                    log_dict["user_name"] = user.name
            result.append(log_dict)
        return result

    @staticmethod
    def record_tab_switch(db: Session, session_id: int, user_id: int) -> Tuple[int, bool]:
        """
        记录切屏事件

        Returns:
            (当前切屏次数, 是否超过限制)
        """
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return 0, False

        # 记录切屏日志
        log = MonitorLog(
            session_id=session_id,
            user_id=user_id,
            exam_id=session.exam_id,
            event_type="tab_switch",
            event_time=datetime.now(),
            detail="考生切换了浏览器标签页",
        )
        db.add(log)
        db.commit()

        # 查询总切屏次数
        count = db.query(MonitorLog).filter(
            MonitorLog.session_id == session_id,
            MonitorLog.event_type == "tab_switch",
        ).count()

        # 检查是否超过限制
        from models.system_config import SystemConfig
        max_count_config = db.query(SystemConfig).filter(
            SystemConfig.config_key == "max_tab_switch_count"
        ).first()
        max_count = int(max_count_config.config_value) if max_count_config else 3

        exceeded = count >= max_count

        # 推送监控更新（异步）
        try:
            import asyncio
            student_data = MonitorService.get_students(db, session.exam_id)
            matching = [s for s in student_data if s["session_id"] == session_id]
            loop = asyncio.get_event_loop()
            if matching:
                loop.create_task(ws_manager.broadcast_to_exam(session.exam_id, {
                    "type": "student_update",
                    "exam_id": session.exam_id,
                    "session_id": session_id,
                    "student": matching[0],
                }))
            # 推送异常事件
            log_data = log.to_dict()
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if user:
                    log_data["username"] = user.username
                    log_data["user_name"] = user.name
            loop.create_task(ws_manager.broadcast_to_exam(session.exam_id, {
                "type": "abnormal_event",
                "exam_id": session.exam_id,
                "event": log_data,
            }))
            # 推送概览更新
            overview_data = MonitorService.get_overview(db, session.exam_id)
            if overview_data:
                loop.create_task(ws_manager.broadcast_to_exam(session.exam_id, {
                    "type": "overview_update",
                    "exam_id": session.exam_id,
                    "overview": overview_data,
                }))
        except Exception:
            pass

        return count, exceeded

    @staticmethod
    async def push_monitor_update(exam_id: int, event_type: str = "update", data: dict = None):
        """推送监控更新"""
        message = {
            "type": event_type,
            "exam_id": exam_id,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        }
        await ws_manager.broadcast_to_exam(exam_id, message)
