# -*- coding: utf-8 -*-
"""系统管理路由 - 系统配置 + 操作日志 + 考试备份/导入 + 系统重置 + 基础数据导出 + 仪表盘"""

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import get_db
from models.user import User
from schemas.system import ConfigUpdate, ConfigBatchUpdate
from services.system_service import SystemService
from utils.security import require_admin

router = APIRouter()

# ============================================================
# 公开接口（无需鉴权）
# ============================================================

@router.get("/exam-notice", summary="获取考试注意事项（公开）")
def get_exam_notice(db: Session = Depends(get_db)):
    """获取全局考试注意事项配置（考生端无需鉴权可调用）"""
    config = SystemService.get_config(db, "exam_notice")
    notice = config.config_value if config else ""
    return {"code": 0, "data": {"notice": notice}, "message": "success"}


@router.get("/configs", summary="获取系统配置")
def get_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取所有系统配置"""
    result = SystemService.get_configs(db)
    # 统一转换为前端期望的 key/value 格式
    front_result = [
        {
            "key": c["config_key"],
            "value": c["config_value"],
            "description": c.get("description") or c["config_key"],
        }
        for c in result
    ]
    return {"code": 0, "data": front_result, "message": "success"}


@router.put("/configs/batch", summary="批量更新系统配置")
def batch_update_configs(
    data: ConfigBatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批量更新系统配置"""
    for item in data.configs:
        key = item.get("key")
        value = item.get("value", "")
        if key:
            SystemService.update_config(db, key, value)
    SystemService.log_operation(db, current_user.id, "批量更新配置", "config", None,
                                f"更新了 {len(data.configs)} 项配置")
    return {"code": 0, "data": None, "message": "配置保存成功"}


@router.put("/configs", summary="更新系统配置")
def update_config(
    data: ConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """更新系统配置"""
    config, message = SystemService.update_config(db, data.config_key, data.config_value, data.description)
    SystemService.log_operation(db, current_user.id, "更新配置", "config", config.id if config else None,
                                f"更新配置: {data.config_key} = {data.config_value}")
    return {"code": 0, "data": config.to_dict() if config else None, "message": message}


@router.get("/operation-logs", summary="获取操作日志")
def get_operation_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int = Query(None),
    action: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取操作日志"""
    result = SystemService.get_operation_logs(db, page, size, user_id, action, start_date, end_date)
    return {"code": 0, "data": result, "message": "success"}


# ============================================================
# 考试数据备份与导入
# ============================================================

class ExportBackupRequest(BaseModel):
    """考试备份导出请求"""
    exam_ids: List[int]


@router.post("/backup/export", summary="导出考试备份")
def export_exam_backup(
    data: ExportBackupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """按选择的考试导出备份 JSON 文件（含考试信息、题目、考生成绩与答卷）"""
    if not data.exam_ids:
        return {"code": 400, "data": None, "message": "请至少选择一场考试"}

    filepath, filename = SystemService.export_exam_backup(db, data.exam_ids)
    if not filepath:
        return {"code": 400, "data": None, "message": filename or "导出失败，未找到有效的考试数据"}
    SystemService.log_operation(
        db, current_user.id, "导出考试备份", "backup", None,
        f"导出了 {len(data.exam_ids)} 场考试备份: {filename}"
    )
    return {"code": 0, "data": {"filename": filename}, "message": "备份导出成功"}


@router.get("/backup/list", summary="备份文件列表")
def list_backups(
    current_user: User = Depends(require_admin),
):
    """获取服务器上的备份文件列表"""
    files = SystemService.list_backups()
    return {"code": 0, "data": files, "message": "success"}


@router.get("/backup/download/{filename}", summary="下载备份文件")
def download_backup(
    filename: str,
    current_user: User = Depends(require_admin),
):
    """下载指定的备份文件（支持 JSON 和 Excel）"""
    filepath = SystemService.get_backup_filepath(filename)
    if not filepath:
        return {"code": 404, "data": None, "message": "备份文件不存在"}
    # 根据文件扩展名自动设置 Content-Type
    if filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        media_type = "application/json"
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type=media_type,
    )


@router.delete("/backup/{filename}", summary="删除备份文件")
def delete_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除指定的备份文件"""
    success, message = SystemService.delete_backup(filename)
    if not success:
        return {"code": 404, "data": None, "message": message}
    SystemService.log_operation(
        db, current_user.id, "删除备份", "backup", None,
        f"删除备份文件: {filename}"
    )
    return {"code": 0, "data": None, "message": message}


@router.post("/backup/import", summary="导入备份文件（解析复盘）")
async def import_exam_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """上传并解析备份文件，返回考试和考生数据摘要供复盘查看"""
    if not file.filename or not (file.filename.endswith(".json") or file.filename.endswith(".xlsx")):
        return {"code": 400, "data": None, "message": "请上传 JSON 或 Excel 格式的备份文件"}

    file_content = await file.read()
    success, message, parsed_data = SystemService.import_exam_backup(file_content, file.filename)
    if not success:
        return {"code": 400, "data": None, "message": message}

    SystemService.log_operation(
        db, current_user.id, "导入备份复盘", "backup", None,
        f"导入备份文件: {file.filename}，包含 {parsed_data.get('exam_count', 0)} 场考试"
    )
    return {"code": 0, "data": parsed_data, "message": message}


@router.post("/backup/restore", summary="恢复考试备份数据")
async def restore_exam_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    上传考试备份文件，将考试、题目、考生成绩和答卷恢复到系统中。
    支持 .xlsx（新格式）和 .json（旧格式）。
    恢复后可在成绩总览中查看。
    """
    if not file.filename or not (file.filename.endswith(".json") or file.filename.endswith(".xlsx")):
        return {"code": 400, "data": None, "message": "请上传 JSON 或 Excel 格式的备份文件"}

    file_content = await file.read()
    success, message, result_data = SystemService.restore_exam_backup(db, file_content, file.filename)
    if not success:
        return {"code": 400, "data": None, "message": message}

    SystemService.log_operation(
        db, current_user.id, "恢复考试备份", "backup", None,
        f"恢复备份文件: {file.filename}，恢复了 {result_data.get('exam_count', 0)} 场考试"
    )
    return {"code": 0, "data": result_data, "message": message}


# ============================================================
# 系统重置
# ============================================================

@router.post("/reset", summary="重置系统到初始状态")
def reset_system(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    重置系统到初始状态：清空所有业务数据，重新写入默认数据。
    ⚠️ 危险操作：不可恢复，请确保已备份重要数据！
    """
    success, message = SystemService.reset_system(db)
    if not success:
        return {"code": 500, "data": None, "message": message}
    return {"code": 0, "data": None, "message": message}


# ============================================================
# 基础数据导出
# ============================================================

@router.post("/backup/export-users", summary="导出用户与班级数据")
def export_users_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """导出全部用户和班级数据到 JSON 文件"""
    filepath, filename = SystemService.export_users_backup(db)
    SystemService.log_operation(
        db, current_user.id, "导出用户班级备份", "backup", None,
        f"导出用户班级数据: {filename}"
    )
    return {"code": 0, "data": {"filename": filename}, "message": "用户班级数据导出成功"}


@router.post("/backup/export-questions", summary="导出题库数据")
def export_questions_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """导出全部题库（分类+题目）数据到 JSON 文件"""
    filepath, filename = SystemService.export_questions_backup(db)
    SystemService.log_operation(
        db, current_user.id, "导出题库备份", "backup", None,
        f"导出题库数据: {filename}"
    )
    return {"code": 0, "data": {"filename": filename}, "message": "题库数据导出成功"}


# ============================================================
# 仪表盘
# ============================================================


@router.get("/dashboard", summary="获取仪表盘数据")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """获取仪表盘数据"""
    result = SystemService.get_dashboard(db)
    return {"code": 0, "data": result, "message": "success"}


@router.get("/about", summary="获取软件版权信息")
def get_about_info():
    """获取软件版权信息（公开接口）"""
    return {
        "code": 0,
        "data": {
            "name": "学习培训考试管理系统",
            "version": "V2.0",
            "author": "lansen",
            "copyright": "开源发布，仅供学习与教学使用",
            "date": "2026年6月2日"
        },
        "message": "success"
    }
