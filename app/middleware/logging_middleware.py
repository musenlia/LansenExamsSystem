# -*- coding: utf-8 -*-
"""操作日志中间件 - 记录关键操作"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import json


# 需要记录日志的 HTTP 方法和路径模式
LOG_METHODS = {"POST", "PUT", "DELETE"}

# 操作动作映射
ACTION_MAP = {
    "POST": "创建",
    "PUT": "更新",
    "DELETE": "删除",
}

# 路径到目标类型的映射
PATH_TARGET_MAP = {
    "/api/users": "user",
    "/api/classes": "class",
    "/api/categories": "category",
    "/api/questions": "question",
    "/api/exams": "exam",
    "/api/sessions": "session",
    "/api/system": "system",
}


class LoggingMiddleware(BaseHTTPMiddleware):
    """操作日志中间件"""

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        response = await call_next(request)

        # 只记录修改操作
        if request.method not in LOG_METHODS:
            return response

        path = request.url.path

        # 排除登录等不需要记录的路径
        if "/auth/" in path:
            return response

        # 尝试记录操作日志
        try:
            user_id = getattr(request.state, "user_id", None)
            if not user_id:
                return response

            # 确定操作目标
            target_type = None
            for prefix, t_type in PATH_TARGET_MAP.items():
                if path.startswith(prefix):
                    target_type = t_type
                    break

            # 提取目标 ID
            target_id = None
            path_parts = [p for p in path.split("/") if p]
            if len(path_parts) >= 4:
                try:
                    target_id = int(path_parts[3])
                except (ValueError, IndexError):
                    pass

            # 构建操作动作
            action_prefix = ACTION_MAP.get(request.method, request.method)
            action = f"{action_prefix}{target_type or ''}"

            # 获取 IP 地址
            ip_address = request.client.host if request.client else None

            # 异步记录日志（非阻塞）
            # 注意：在中间件中获取 db 会话比较复杂，
            # 这里使用后台任务方式
            from database import SessionLocal
            from services.system_service import SystemService
            db = SessionLocal()
            try:
                SystemService.log_operation(
                    db=db,
                    user_id=user_id,
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    detail=f"{request.method} {path}",
                    ip_address=ip_address,
                )
            except Exception:
                pass  # 日志记录失败不影响主流程
            finally:
                db.close()

        except Exception:
            pass  # 日志中间件异常不影响主流程

        return response
