# -*- coding: utf-8 -*-
"""监控路由 - 监控总览 + 考生列表 + 强制交卷 + 异常事件 + WebSocket"""

import asyncio
import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.monitor import ForceSubmitRequest, ExtraTimeRequest
from services.monitor_service import MonitorService, ws_manager
from services.session_service import SessionService
from services.system_service import SystemService
from utils.security import require_admin, require_admin_or_teacher

router = APIRouter()


@router.get("/exams/{exam_id}/overview", summary="获取监控总览")
def get_monitor_overview(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取考试监控总览"""
    result = MonitorService.get_overview(db, exam_id)
    if not result:
        return {"code": 404, "data": None, "message": "考试不存在"}
    return {"code": 0, "data": result, "message": "success"}


@router.get("/exams/{exam_id}/students", summary="获取考生进度列表")
def get_monitor_students(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取考生进度列表（管理员和教师均可查看全部考生数据）"""
    result = MonitorService.get_students(db, exam_id)
    return {"code": 0, "data": result, "message": "success"}


@router.post("/sessions/{session_id}/force-submit", summary="强制交卷")
async def force_submit(
    session_id: int,
    data: ForceSubmitRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """强制某考生交卷"""
    reason = data.reason if data else "管理员强制交卷"
    success, message = SessionService.force_submit(db, session_id, reason)
    if not success:
        return {"code": 400, "data": None, "message": message}

    # 获取会话信息用于推送
    from models.session import ExamSession
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()

    SystemService.log_operation(
        db, current_user.id, "强制交卷", "session", session_id,
        f"强制交卷会话ID: {session_id}, 原因: {reason}"
    )

    # 推送 WebSocket 通知
    if session:
        # 推送强制交卷事件
        await ws_manager.broadcast_to_exam(session.exam_id, {
            "type": "force_submit",
            "session_id": session_id,
            "user_id": session.user_id,
            "reason": reason,
        })
        # 推送概览更新
        overview = MonitorService.get_overview(db, session.exam_id)
        if overview:
            await ws_manager.broadcast_to_exam(session.exam_id, {
                "type": "overview_update",
                "exam_id": session.exam_id,
                "overview": overview,
            })

    return {"code": 0, "data": None, "message": message}


@router.post("/sessions/{session_id}/reset", summary="重置考试(重考)")
async def reset_exam(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """重置已交卷考生的会话为未开始状态，清空答题记录和分数"""
    success, message = SessionService.reset_exam(db, session_id)
    if not success:
        return {"code": 400, "data": None, "message": message}

    from models.session import ExamSession
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()

    SystemService.log_operation(
        db, current_user.id, "重置考试", "session", session_id,
        f"重置考试会话ID: {session_id}"
    )

    if session:
        await ws_manager.broadcast_to_exam(session.exam_id, {
            "type": "session_reset",
            "session_id": session_id,
            "user_id": session.user_id,
        })
        overview = MonitorService.get_overview(db, session.exam_id)
        if overview:
            await ws_manager.broadcast_to_exam(session.exam_id, {
                "type": "overview_update",
                "exam_id": session.exam_id,
                "overview": overview,
            })

    return {"code": 0, "data": None, "message": message}


@router.post("/sessions/{session_id}/resume", summary="恢复续考")
async def resume_exam(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """恢复已交卷/超时的考生会话为答题中状态，保留答题记录"""
    success, message = SessionService.resume_exam(db, session_id)
    if not success:
        return {"code": 400, "data": None, "message": message}

    from models.session import ExamSession
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()

    SystemService.log_operation(
        db, current_user.id, "恢复续考", "session", session_id,
        f"恢复续考会话ID: {session_id}"
    )

    if session:
        await ws_manager.broadcast_to_exam(session.exam_id, {
            "type": "session_resume",
            "session_id": session_id,
            "user_id": session.user_id,
        })
        overview = MonitorService.get_overview(db, session.exam_id)
        if overview:
            await ws_manager.broadcast_to_exam(session.exam_id, {
                "type": "overview_update",
                "exam_id": session.exam_id,
                "overview": overview,
            })

    return {"code": 0, "data": None, "message": message}


@router.post("/sessions/{session_id}/extra-time", summary="补时")
async def add_extra_time(
    session_id: int,
    data: ExtraTimeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """为正在答题的考生增加额外考试时间"""
    success, message = SessionService.add_extra_time(db, session_id, data.extra_minutes)
    if not success:
        return {"code": 400, "data": None, "message": message}

    from models.session import ExamSession
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()

    SystemService.log_operation(
        db, current_user.id, "补时", "session", session_id,
        f"补时会话ID: {session_id}, 增加时间: {data.extra_minutes}分钟"
    )

    if session:
        await ws_manager.broadcast_to_exam(session.exam_id, {
            "type": "extra_time_added",
            "session_id": session_id,
            "user_id": session.user_id,
            "extra_minutes": data.extra_minutes,
        })

    return {"code": 0, "data": {"extra_time": data.extra_minutes}, "message": message}


@router.get("/exams/{exam_id}/abnormal", summary="获取异常事件")
def get_abnormal_events(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取异常事件列表"""
    result = MonitorService.get_abnormal_events(db, exam_id)
    return {"code": 0, "data": result, "message": "success"}


@router.websocket("/ws/monitor/{exam_id}")
async def websocket_monitor(websocket: WebSocket, exam_id: int):
    """WebSocket 监控连接"""
    await ws_manager.connect(websocket, exam_id)
    try:
        while True:
            # 接收客户端消息（心跳等）
            data = await websocket.receive_text()
            # 回复心跳 pong
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, exam_id)
