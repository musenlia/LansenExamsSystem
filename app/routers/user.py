# -*- coding: utf-8 -*-
"""用户管理路由 - CRUD + 导入 + 重置密码 + 导出模板 + 批量操作"""

from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import io

from database import get_db
from models.user import User
from schemas.user import UserCreate, UserUpdate
from services.user_service import UserService
from services.import_export_service import ImportExportService
from services.system_service import SystemService
from utils.security import get_current_user, require_admin

router = APIRouter()


class BatchUserRequest(BaseModel):
    """批量用户操作请求"""
    ids: List[int]


@router.get("", summary="获取用户列表")
def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    role: str = Query(None),
    class_id: int = Query(None),
    status: str = Query(None),
    sort_by: str = Query("id", description="排序字段: id/username/name/role/created_at"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取用户列表（分页+筛选+排序）"""
    result = UserService.get_list(db, page, size, keyword, role, class_id, status, sort_by, sort_order)
    return {"code": 0, "data": result, "message": "success"}


@router.post("/import", summary="批量导入用户")
def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批量导入用户"""
    file_data = file.file.read()
    result = UserService.batch_import(db, file_data)
    SystemService.log_operation(db, current_user.id, "导入用户", "user", None, f"导入{result['success_count']}个用户")
    return {"code": 0, "data": result, "message": "success"}


@router.get("/export-template", summary="下载用户导入模板")
def export_user_template(current_user: User = Depends(require_admin)):
    """下载用户导入模板"""
    template_data = ImportExportService.get_user_template()
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=user_import_template.xlsx"},
    )


@router.post("/batch-delete", summary="批量删除用户")
def batch_delete_users(
    data: BatchUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批量删除用户（跳过最后一个管理员）"""
    result = UserService.batch_delete(db, data.ids)
    SystemService.log_operation(
        db, current_user.id, "批量删除用户", "user", None,
        f"批量删除用户: 成功{result['success_count']}个，失败{result['fail_count']}个"
    )
    return {"code": 0, "data": result, "message": "success"}


@router.post("/batch-reset-password", summary="批量重置密码")
def batch_reset_password(
    data: BatchUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批量重置密码为默认值 123456"""
    result = UserService.batch_reset_password(db, data.ids)
    SystemService.log_operation(
        db, current_user.id, "批量重置密码", "user", None,
        f"批量重置密码: 成功{result['success_count']}个，失败{result['fail_count']}个"
    )
    return {"code": 0, "data": result, "message": "success"}


# 注意：/{user_id} 动态路径必须放在固定路径之后，否则会拦截 /import、/export-template 等
@router.get("/{user_id}", summary="获取用户详情")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取用户详情"""
    user = UserService.get_by_id(db, user_id)
    if not user:
        return {"code": 404, "data": None, "message": "用户不存在"}
    user_dict = UserService.get_user_with_class(db, user)
    return {"code": 0, "data": user_dict, "message": "success"}


@router.post("", summary="创建用户")
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建用户"""
    user, message = UserService.create(db, data.model_dump())
    if not user:
        return {"code": 400, "data": None, "message": message}
    user_dict = UserService.get_user_with_class(db, user)
    SystemService.log_operation(db, current_user.id, "创建用户", "user", user.id, f"创建用户: {user.username}")
    return {"code": 0, "data": user_dict, "message": message}


@router.put("/{user_id}", summary="更新用户")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """更新用户"""
    user, message = UserService.update(db, user_id, data.model_dump(exclude_none=True))
    if not user:
        return {"code": 400, "data": None, "message": message}
    user_dict = UserService.get_user_with_class(db, user)
    SystemService.log_operation(db, current_user.id, "更新用户", "user", user.id, f"更新用户: {user.username}")
    return {"code": 0, "data": user_dict, "message": message}


@router.delete("/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除用户"""
    success, message = UserService.delete(db, user_id)
    if not success:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "删除用户", "user", user_id, f"删除用户ID: {user_id}")
    return {"code": 0, "data": None, "message": message}


@router.post("/{user_id}/reset-password", summary="重置用户密码")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """重置用户密码为默认值 123456"""
    success, message = UserService.reset_password(db, user_id)
    if not success:
        return {"code": 400, "data": None, "message": message}
    SystemService.log_operation(db, current_user.id, "重置密码", "user", user_id, f"重置用户ID: {user_id} 的密码")
    return {"code": 0, "data": None, "message": message}
