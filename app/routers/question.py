# -*- coding: utf-8 -*-
"""题库管理路由 - CRUD + 导入 + 导出模板 + 统计 + 批量操作"""

from typing import List as TypingList
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import io

from database import get_db
from models.user import User
from schemas.question import QuestionCreate, QuestionUpdate
from services.question_service import QuestionService
from services.import_export_service import ImportExportService
from services.system_service import SystemService
from utils.security import require_admin

router = APIRouter()


@router.get("", summary="获取题目列表")
def get_questions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    type: str = Query(None),
    difficulty: str = Query(None),
    category_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取题目列表"""
    result = QuestionService.get_list(db, page, size, keyword, type, difficulty, category_id)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/stats", summary="获取题目统计")
def get_question_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取题目统计"""
    result = QuestionService.get_stats(db)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/export-template", summary="下载题目导入模板")
def export_question_template(current_user: User = Depends(require_admin)):
    """下载题目导入模板"""
    template_data = ImportExportService.get_question_template()
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=question_import_template.xlsx"},
    )


@router.post("/import", summary="批量导入题目")
def import_questions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批量导入题目"""
    file_data = file.file.read()
    result = QuestionService.batch_import(db, file_data)
    SystemService.log_operation(db, current_user.id, "导入题目", "question", None, f"导入{result['success_count']}道题目")
    return {"code": 0, "data": result, "message": "success"}


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: TypingList[int]


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    ids: TypingList[int]
    category_id: int | None = None
    difficulty: str | None = None


@router.post("/batch-delete", summary="批量删除题目")
def batch_delete_questions(
    data: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批量删除题目"""
    success_count = 0
    fail_count = 0
    errors = []
    for qid in data.ids:
        ok, msg = QuestionService.delete(db, qid)
        if ok:
            success_count += 1
        else:
            fail_count += 1
            errors.append({"id": qid, "reason": msg})
    SystemService.log_operation(db, current_user.id, "批量删除题目", "question", None, f"删除{success_count}道题目")
    return {"code": 0, "data": {"success_count": success_count, "fail_count": fail_count, "errors": errors}, "message": "success"}


@router.post("/batch-update", summary="批量更新题目")
def batch_update_questions(
    data: BatchUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批量更新题目（修改分类/难度）"""
    update_data = {}
    if data.category_id is not None:
        update_data["category_id"] = data.category_id
    if data.difficulty is not None:
        update_data["difficulty"] = data.difficulty

    if not update_data:
        return {"code": 400, "data": None, "message": "未指定更新内容"}

    success_count = 0
    fail_count = 0
    for qid in data.ids:
        q, msg = QuestionService.update(db, qid, update_data)
        if q:
            success_count += 1
        else:
            fail_count += 1

    SystemService.log_operation(db, current_user.id, "批量更新题目", "question", None, f"更新{success_count}道题目")
    return {"code": 0, "data": {"success_count": success_count, "fail_count": fail_count}, "message": "success"}


# 注意：/{question_id} 动态路径必须放在固定路径之后，否则会拦截 /stats、/export-template 等
@router.get("/{question_id}", summary="获取题目详情")
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取题目详情"""
    q = QuestionService.get_by_id(db, question_id)
    if not q:
        return {"code": 404, "data": None, "message": "题目不存在"}
    q_dict = q.to_dict()
    if q.category_id:
        from models.category import Category
        cat = db.query(Category).filter(Category.id == q.category_id).first()
        q_dict["category_name"] = cat.name if cat else None
    return {"code": 0, "data": q_dict, "message": "success"}


@router.post("", summary="创建题目")
def create_question(
    data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建题目"""
    q, message = QuestionService.create(db, data.model_dump())
    if not q:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "创建题目", "question", q.id, f"创建题目: {q.content[:20]}")
    return {"code": 0, "data": q.to_dict(), "message": message}


@router.put("/{question_id}", summary="更新题目")
def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """更新题目"""
    q, message = QuestionService.update(db, question_id, data.model_dump(exclude_none=True))
    if not q:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "更新题目", "question", question_id, f"更新题目ID: {question_id}")
    return {"code": 0, "data": q.to_dict(), "message": message}


@router.delete("/{question_id}", summary="删除题目")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除题目"""
    success, message = QuestionService.delete(db, question_id)
    if not success:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "删除题目", "question", question_id, f"删除题目ID: {question_id}")
    return {"code": 0, "data": None, "message": message}
