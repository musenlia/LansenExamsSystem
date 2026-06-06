# -*- coding: utf-8 -*-
"""考试会话路由 - 我的考试 + 进入考试 + 获取题目 + 保存答案 + 提交 + 结果"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.exam import Exam
from schemas.session import SubmitRequest
from schemas.answer import AnswerSaveRequest
from services.session_service import SessionService
from utils.security import get_current_user

router = APIRouter()


@router.get("/my-exams", summary="获取我的考试列表")
def get_my_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考生的考试列表"""
    result = SessionService.get_my_exams(db, current_user.id)
    return {"code": 0, "data": result, "message": "success"}


@router.post("/enter", summary="进入考试")
def enter_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """进入考试（创建或恢复会话）"""
    session, message = SessionService.enter_exam(db, current_user.id, exam_id)
    if not session:
        return {"code": 400, "data": None, "message": message}

    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    from datetime import datetime
    remaining = None
    if session.start_time and exam and exam.duration:
        elapsed = (datetime.now() - session.start_time).total_seconds()
        remaining = max(0, int(exam.duration * 60 - elapsed))

    return {
        "code": 0,
        "data": {
            "session_id": session.id,
            "exam_name": exam.name if exam else "",
            "duration": exam.duration if exam else 0,
            "total_score": exam.total_score if exam else 0,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "remaining_seconds": remaining,
            "status": session.status,
        },
        "message": message,
    }


@router.get("/{session_id}/questions", summary="获取考试题目")
def get_session_questions(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考试题目列表（考生视角，不含正确答案）"""
    result = SessionService.get_questions(db, session_id, current_user.id)
    if not result:
        return {"code": 400, "data": None, "message": "获取题目失败"}
    if result.get("_timeout"):
        return {"code": 408, "data": {"session_id": result["session_id"], "auto_submitted": True}, "message": "考试已超时，已自动交卷"}
    return {"code": 0, "data": result, "message": "success"}


@router.put("/{session_id}/answers/{question_id}", summary="保存答案")
def save_answer(
    session_id: int,
    question_id: int,
    data: AnswerSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """保存单题答案"""
    success, message, extra = SessionService.save_answer(
        db, session_id, question_id, current_user.id, data.user_answer
    )
    if not success:
        code = 408 if extra and extra.get("auto_submitted") else 400
        return {"code": code, "data": extra, "message": message}
    return {"code": 0, "data": extra, "message": message}


@router.post("/{session_id}/submit", summary="提交答卷")
def submit_exam(
    session_id: int,
    data: SubmitRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交答卷"""
    success, message, result_data = SessionService.submit_exam(db, session_id, current_user.id)
    if not success:
        return {"code": 400, "data": None, "message": message}
    return {"code": 0, "data": result_data, "message": message}


@router.get("/{session_id}/result", summary="获取考试结果")
def get_exam_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考试结果（按角色返回不同数据）"""
    result = SessionService.get_result(db, session_id, current_user.id, current_user.role)
    if not result:
        return {"code": 400, "data": None, "message": "获取结果失败"}
    return {"code": 0, "data": result, "message": "success"}


@router.post("/{session_id}/tab-switch", summary="上报切屏")
def report_tab_switch(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上报切屏事件"""
    from services.monitor_service import MonitorService
    count, exceeded = MonitorService.record_tab_switch(db, session_id, current_user.id)

    # 切屏超限时后端自动交卷
    if exceeded:
        from services.session_service import SessionService
        success, msg, _ = SessionService.submit_exam(db, session_id, current_user.id)

    return {
        "code": 0,
        "data": {"tab_switch_count": count, "exceeded": exceeded},
        "message": "切屏次数超过限制，已被强制交卷" if exceeded else "success",
    }


@router.put("/{session_id}/flag/{question_id}", summary="标记/取消标记题目")
def toggle_question_flag(
    session_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """切换题目标记状态"""
    # 先读取当前状态，再取反
    from models.answer import Answer
    answer = db.query(Answer).filter(
        Answer.session_id == session_id,
        Answer.question_id == question_id,
    ).first()
    new_flagged = not (bool(answer.is_flagged) if answer and answer.is_flagged else False)

    success, message, flag_state = SessionService.toggle_flag(
        db, session_id, question_id, current_user.id, new_flagged
    )
    if not success:
        return {"code": 400, "data": None, "message": message}
    return {"code": 0, "data": {"is_flagged": flag_state}, "message": message}
