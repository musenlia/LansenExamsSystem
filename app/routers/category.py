# -*- coding: utf-8 -*-
"""分类管理路由 - 树形CRUD"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.category import CategoryCreate, CategoryUpdate
from services.category_service import CategoryService
from services.system_service import SystemService
from utils.security import require_admin

router = APIRouter()


@router.get("/tree", summary="获取分类树")
def get_category_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取分类树形结构"""
    tree = CategoryService.get_tree(db)
    return {"code": 0, "data": tree, "message": "success"}


@router.get("", summary="获取分类列表")
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取分类扁平列表"""
    result = CategoryService.get_list(db)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/{category_id}", summary="获取分类详情")
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取分类详情"""
    cat = CategoryService.get_by_id(db, category_id)
    if not cat:
        return {"code": 404, "data": None, "message": "分类不存在"}
    return {"code": 0, "data": cat.to_dict(), "message": "success"}


@router.post("", summary="创建分类")
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建分类"""
    cat, message = CategoryService.create(db, data.model_dump())
    if not cat:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "创建分类", "category", cat.id, f"创建分类: {cat.name}")
    return {"code": 0, "data": cat.to_dict(), "message": message}


@router.put("/{category_id}", summary="更新分类")
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """更新分类"""
    cat, message = CategoryService.update(db, category_id, data.model_dump(exclude_none=True))
    if not cat:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "更新分类", "category", category_id, f"更新分类: {cat.name}")
    return {"code": 0, "data": cat.to_dict(), "message": message}


@router.delete("/{category_id}", summary="删除分类")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除分类"""
    success, message = CategoryService.delete(db, category_id)
    if not success:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "删除分类", "category", category_id, f"删除分类ID: {category_id}")
    return {"code": 0, "data": None, "message": message}
