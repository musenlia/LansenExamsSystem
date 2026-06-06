# -*- coding: utf-8 -*-
"""班级管理路由 - CRUD"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.class_ import ClassCreate, ClassUpdate
from services.class_service import ClassService
from services.system_service import SystemService
from utils.security import require_admin, require_admin_or_teacher

router = APIRouter()


@router.get("", summary="获取班级列表")
def get_classes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取班级列表（管理员和教师可查看）"""
    result = ClassService.get_list(db, page, size, keyword)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/all", summary="获取所有班级（下拉选择用）")
def get_all_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取所有班级（管理员和教师可查看）"""
    result = ClassService.get_all(db)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/{class_id}", summary="获取班级详情")
def get_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher),
):
    """获取班级详情（管理员和教师可查看）"""
    cls = ClassService.get_by_id(db, class_id)
    if not cls:
        return {"code": 404, "data": None, "message": "班级不存在"}

    cls_dict = cls.to_dict()
    students = ClassService.get_students(db, class_id)
    from models.user import User
    student_count = db.query(User).filter(User.class_id == class_id).count()
    cls_dict["student_count"] = student_count
    cls_dict["students"] = students

    return {"code": 0, "data": cls_dict, "message": "success"}


@router.post("", summary="创建班级")
def create_class(
    data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建班级"""
    cls, message = ClassService.create(db, data.model_dump())
    if not cls:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "创建班级", "class", cls.id, f"创建班级: {cls.name}")
    return {"code": 0, "data": cls.to_dict(), "message": message}


@router.put("/{class_id}", summary="更新班级")
def update_class(
    class_id: int,
    data: ClassUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """更新班级"""
    cls, message = ClassService.update(db, class_id, data.model_dump(exclude_none=True))
    if not cls:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "更新班级", "class", class_id, f"更新班级: {cls.name}")
    return {"code": 0, "data": cls.to_dict(), "message": message}


@router.delete("/{class_id}", summary="删除班级")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除班级"""
    success, message = ClassService.delete(db, class_id)
    if not success:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "删除班级", "class", class_id, f"删除班级ID: {class_id}")
    return {"code": 0, "data": None, "message": message}
