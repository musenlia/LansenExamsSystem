# -*- coding: utf-8 -*-
"""JWT 认证中间件 - 白名单路径排除"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from utils.security import decode_access_token

# 白名单路径（不需要认证）
WHITE_LIST = [
    "/api/auth/login",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/api/health",
    "/api/system/exam-notice",  # 考试注意事项公开读取
]


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 认证中间件"""

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        path = request.url.path

        # 静态文件和 WebSocket 跳过
        if path.startswith("/assets") or path.endswith((".js", ".css", ".ico", ".png", ".jpg")):
            return await call_next(request)

        if path.startswith("/api/ws/"):
            return await call_next(request)

        # 白名单路径跳过认证
        if path in WHITE_LIST:
            return await call_next(request)

        # 非 API 路径（前端路由）跳过
        if not path.startswith("/api/"):
            return await call_next(request)

        # 检查 Authorization 头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "data": None, "message": "未提供认证凭据"},
            )

        # 解析 Bearer Token
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"code": 401, "data": None, "message": "认证格式错误"},
            )

        token = parts[1]
        payload = decode_access_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"code": 401, "data": None, "message": "Token 无效或已过期"},
            )

        # 将用户信息存入 request state
        request.state.user_id = payload.get("user_id")
        request.state.username = payload.get("username")
        request.state.role = payload.get("role")

        return await call_next(request)
