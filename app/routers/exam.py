# -*- coding: utf-8 -*-
"""考试管理路由 - CRUD + 题目 + 发布 + 暂停 + 恢复 + 终止 + 预览"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import get_db
from models.user import User
from schemas.exam import ExamCreate, ExamUpdate
from services.exam_service import ExamService
from services.system_service import SystemService
from utils.security import require_admin, require_admin_or_teacher

router = APIRouter()


class ExamQuestionItem(BaseModel):
    """考试题目设置项"""
    question_id: int
    score: float = 0


class SetExamQuestionsRequest(BaseModel):
    """设置考试题目请求"""
    questions: List[ExamQuestionItem]


@router.get("", summary="获取考试列表")
def get_exams(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    status: str = Query(None),
    mode: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取考试列表（管理员和教师可查看）"""
    result = ExamService.get_list(db, page, size, keyword, status, mode)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/{exam_id}", summary="获取考试详情")
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取考试详情（管理员和教师可查看）"""
    result = ExamService.get_detail(db, exam_id)
    if not result:
        return {"code": 404, "data": None, "message": "考试不存在"}
    return {"code": 0, "data": result, "message": "success"}


@router.post("", summary="创建考试")
def create_exam(
    data: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建考试"""
    exam, message = ExamService.create(db, data.model_dump(), current_user.id)
    if not exam:
        return {"code": 400, "data": None, "message": message}
    result = ExamService.get_detail(db, exam.id)
    SystemService.log_operation(db, current_user.id, "创建考试", "exam", exam.id, f"创建考试: {exam.name}")
    return {"code": 0, "data": result, "message": message}


@router.put("/{exam_id}", summary="更新考试")
def update_exam(
    exam_id: int,
    data: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """更新考试"""
    exam, message = ExamService.update(db, exam_id, data.model_dump(exclude_none=True))
    if not exam:
        return {"code": 400, "data": None, "message": message}
    result = ExamService.get_detail(db, exam.id)
    SystemService.log_operation(db, current_user.id, "更新考试", "exam", exam_id, f"更新考试: {exam.name}")
    return {"code": 0, "data": result, "message": message}


@router.delete("/{exam_id}", summary="删除考试", description="删除考试（允许删除所有状态的考试，已发布/进行中的考试删除后所有相关数据将不可恢复）")
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除考试"""
    success, message = ExamService.delete(db, exam_id)
    if not success:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "删除考试", "exam", exam_id, f"删除考试ID: {exam_id}")
    return {"code": 0, "data": None, "message": message}


@router.get("/{exam_id}/questions", summary="获取考试题目列表")
def get_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取考试题目列表"""
    result = ExamService.get_exam_questions_for_admin(db, exam_id)
    return {"code": 0, "data": result, "message": "success"}


@router.post("/{exam_id}/questions", summary="设置考试题目")
def set_exam_questions(
    exam_id: int,
    data: SetExamQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """设置考试题目（仅草稿状态可设置）"""
    question_list = [{"question_id": q.question_id, "score": q.score} for q in data.questions]
    success, message = ExamService.set_exam_questions(db, exam_id, question_list)
    if not success:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "设置考试题目", "exam", exam_id, f"设置考试题目，共{len(question_list)}题")
    return {"code": 0, "data": None, "message": message}


@router.post("/{exam_id}/publish", summary="发布考试")
def publish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """发布考试"""
    exam, message = ExamService.publish(db, exam_id)
    if not exam:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "发布考试", "exam", exam_id, f"发布考试: {exam.name}")
    return {"code": 0, "data": exam.to_dict(), "message": message}


@router.post("/{exam_id}/pause", summary="暂停考试")
def pause_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """暂停考试"""
    exam, message = ExamService.pause(db, exam_id)
    if not exam:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "暂停考试", "exam", exam_id, f"暂停考试: {exam.name}")
    return {"code": 0, "data": exam.to_dict(), "message": message}


@router.post("/{exam_id}/resume", summary="恢复考试")
def resume_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """恢复考试"""
    exam, message = ExamService.resume(db, exam_id)
    if not exam:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "恢复考试", "exam", exam_id, f"恢复考试: {exam.name}")
    return {"code": 0, "data": exam.to_dict(), "message": message}


@router.post("/{exam_id}/terminate", summary="终止考试")
def terminate_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """终止考试"""
    exam, message = ExamService.terminate(db, exam_id)
    if not exam:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "终止考试", "exam", exam_id, f"终止考试: {exam.name}")
    return {"code": 0, "data": exam.to_dict(), "message": message}


@router.post("/{exam_id}/reactivate", summary="重新激活考试")
def reactivate_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """重新激活已结束或已归档的考试"""
    exam, message = ExamService.reactivate(db, exam_id)
    if not exam:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "重新激活考试", "exam", exam_id, f"重新激活考试: {exam.name}")
    return {"code": 0, "data": exam.to_dict(), "message": message}


@router.get("/{exam_id}/preview", summary="预览考试")
def preview_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """预览考试（管理员视角，含正确答案）"""
    result = ExamService.get_detail(db, exam_id)
    if not result:
        return {"code": 404, "data": None, "message": "考试不存在"}
    return {"code": 0, "data": result, "message": "success"}
