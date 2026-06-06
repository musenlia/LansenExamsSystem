# -*- coding: utf-8 -*-
"""学习培训考试管理系统 - FastAPI 应用入口"""

import os
import yaml
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.requests import Request

# 加载配置
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    """加载 YAML 配置文件"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

app = FastAPI(
    title="学习培训考试管理系统",
    description="Training Exam Management System API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["server"]["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 操作日志中间件
from middleware.logging_middleware import LoggingMiddleware
app.add_middleware(LoggingMiddleware)

# JWT 认证中间件（在日志中间件之后注册，先执行）
from middleware.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)

# =============================================
# 路由注册
# =============================================
from routers import auth, user, class_, category, question, exam, session, monitor, score, system

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(user.router, prefix="/api/users", tags=["用户管理"])
app.include_router(class_.router, prefix="/api/classes", tags=["班级管理"])
app.include_router(category.router, prefix="/api/categories", tags=["分类管理"])
app.include_router(question.router, prefix="/api/questions", tags=["题库管理"])
app.include_router(exam.router, prefix="/api/exams", tags=["考试管理"])
app.include_router(session.router, prefix="/api/sessions", tags=["考试会话"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["实时监控"])
app.include_router(score.router, prefix="/api/scores", tags=["成绩管理"])
app.include_router(system.router, prefix="/api/system", tags=["系统设置"])


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "data": None,
            "message": f"服务器内部错误: {str(exc)}",
        },
    )


# 健康检查
@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {"code": 0, "data": {"status": "ok"}, "message": "success"}


# 静态文件托管（前端构建产物）— SPA fallback
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    # 1. 挂载 /assets 目录（JS/CSS 等静态资源）
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # 2. SPA fallback: 所有非 /api/ 的 GET 请求尝试匹配静态文件，否则返回 index.html
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """SPA 路由兜底 — 非API请求返回 index.html"""
        # 跳过 API 路径（交给 API 路由处理）
        if full_path.startswith("api/"):
            return JSONResponse(
                status_code=404,
                content={"code": 404, "data": None, "message": "Not Found"},
            )
        # 尝试匹配静态文件（如 vite.svg, admin.html 等根目录文件）
        file_path = STATIC_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        # 否则返回 index.html，让 React Router 处理路由
        return FileResponse(str(STATIC_DIR / "index.html"))


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("=" * 60)
    print("  学习培训考试管理系统 - 服务已启动")
    print("  版本号: V2.0")
    print("  研发作者: lansen")
    print("  使用权: 开源发布，仅供学习与教学使用")
    print("  日期: 2026年6月2日")
    print(f"  API 文档: http://localhost:{config['server']['port']}/api/docs")
    print(f"  健康检查: http://localhost:{config['server']['port']}/api/health")
    print(f"  关于信息: http://localhost:{config['server']['port']}/api/system/about")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=config["server"]["debug"],
    )
