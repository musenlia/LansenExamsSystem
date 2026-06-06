# -*- coding: utf-8 -*-
"""成绩管理路由 - 成绩列表 + 答卷详情 + 统计 + 导出"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from database import get_db
from models.user import User
from services.score_service import ScoreService
from services.system_service import SystemService
from utils.security import require_admin_or_teacher

router = APIRouter()


@router.get("/exams/{exam_id}", summary="获取考试成绩列表")
def get_score_list(
    exam_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    class_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取考试成绩列表（管理员可查看全部，教师仅本班）"""
    # 教师角色：强制按班级过滤
    if current_user.role == "teacher":
        teacher_class_id = class_id if class_id else current_user.class_id
        result = ScoreService.get_score_list(db, exam_id, page, size, keyword, teacher_class_id)
    else:
        result = ScoreService.get_score_list(db, exam_id, page, size, keyword, class_id)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/sessions/{session_id}", summary="获取答卷详情")
def get_score_detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取答卷详情（教师仅可查看本班学生）"""
    from models.session import ExamSession
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        return {"code": 404, "data": None, "message": "答卷不存在"}

    # 教师角色：验证被查看学生是否在本班
    if current_user.role == "teacher" and current_user.class_id is not None:
        student = db.query(User).filter(User.id == session.user_id).first()
        if student and student.class_id != current_user.class_id:
            return {"code": 403, "data": None, "message": "仅可查看本班学生的答卷"}

    result = ScoreService.get_score_detail(db, session_id)
    if not result:
        return {"code": 404, "data": None, "message": "答卷不存在"}
    return {"code": 0, "data": result, "message": "success"}


@router.get("/exams/{exam_id}/stats", summary="获取成绩统计")
def get_score_stats(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取成绩统计"""
    result = ScoreService.get_stats(db, exam_id)
    if not result:
        return {"code": 404, "data": None, "message": "考试不存在"}
    return {"code": 0, "data": result, "message": "success"}


@router.get("/exams/{exam_id}/export", summary="导出成绩")
def export_scores(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """导出成绩 Excel"""
    result = ScoreService.export_scores(db, exam_id)
    if not result:
        return {"code": 404, "data": None, "message": "导出失败"}
    return StreamingResponse(
        io.BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=exam_{exam_id}_scores.xlsx"},
    )
