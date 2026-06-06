# -*- coding: utf-8 -*-
"""数据库连接引擎、会话管理、依赖注入 — SQLite 版本"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator

# 数据库文件存放路径（与 server/ 同级）
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'exam_system.db'}"

# 创建引擎（SQLite 不需要连接池，check_same_thread=False 允许 FastAPI 多线程访问）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类"""
    pass


def get_db() -> Generator:
    """
    FastAPI 依赖注入：获取数据库会话

    使用方式：
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库（创建所有表）"""
    # 导入所有模型以确保它们被注册
    from models import (  # noqa: F401
        User, Class, Category, Question,
        Exam, ExamQuestion, ExamClass,
        ExamSession, Answer, MonitorLog,
        SystemConfig, OperationLog,
    )
    Base.metadata.create_all(bind=engine)
