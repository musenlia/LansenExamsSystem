# -*- coding: utf-8 -*-
"""初始数据脚本 - 创建默认管理员、系统默认参数（SQLite 版本）"""

import sys
import os
from pathlib import Path

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base, init_db
from models.user import User
from models.class_ import Class
from models.category import Category
from models.system_config import SystemConfig
from utils.security import get_password_hash


def seed_admin_user(db: Session) -> None:
    """创建默认管理员账号"""
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print("  [跳过] 管理员账号已存在")
        return

    admin = User(
        username="admin",
        name="系统管理员",
        password=get_password_hash("admin123"),
        role="admin",
        class_id=None,
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(admin)
    db.commit()
    print("  [完成] 创建默认管理员账号: admin / admin123")


def seed_default_classes(db: Session) -> None:
    """创建默认班级"""
    existing = db.query(Class).first()
    if existing:
        print("  [跳过] 班级数据已存在")
        return

    classes = [
        Class(name="默认班级", description="系统默认班级", created_at=datetime.now(), updated_at=datetime.now()),
        Class(name="2026年春季班", description="2026年春季培训班级", created_at=datetime.now(), updated_at=datetime.now()),
    ]
    db.add_all(classes)
    db.commit()
    print("  [完成] 创建默认班级数据")


def seed_default_categories(db: Session) -> None:
    """创建默认题目分类"""
    existing = db.query(Category).first()
    if existing:
        print("  [跳过] 分类数据已存在")
        return

    categories = [
        Category(name="高等教育心理学", parent_id=None, description="高等教育心理学相关知识点", sort_order=1, created_at=datetime.now()),
        Category(name="高等教育学", parent_id=None, description="高等教育学相关知识点", sort_order=2, created_at=datetime.now()),
        Category(name="高等学校教师职业道德修养", parent_id=None, description="高校教师职业道德与修养", sort_order=3, created_at=datetime.now()),
        Category(name="教育教学技能", parent_id=None, description="教育教学技能与方法", sort_order=4, created_at=datetime.now()),
        Category(name="高等教育法规概论", parent_id=None, description="高等教育法律法规与政策", sort_order=5, created_at=datetime.now()),
        Category(name="现代教育技术学", parent_id=None, description="现代教育技术及其应用", sort_order=6, created_at=datetime.now()),
    ]
    db.add_all(categories)
    db.commit()
    print("  [完成] 创建默认题目分类")


def seed_system_configs(db: Session) -> None:
    """创建系统默认配置"""
    existing = db.query(SystemConfig).first()
    if existing:
        print("  [跳过] 系统配置已存在")
        return

    configs = [
        SystemConfig(
            config_key="exam_auto_submit_minutes",
            config_value="5",
            description="考试结束前自动提交时间(分钟)",
            updated_at=datetime.now(),
        ),
        SystemConfig(
            config_key="max_tab_switch_count",
            config_value="3",
            description="切屏最大次数",
            updated_at=datetime.now(),
        ),
        SystemConfig(
            config_key="session_timeout_minutes",
            config_value="120",
            description="会话超时时间(分钟)",
            updated_at=datetime.now(),
        ),
        SystemConfig(
            config_key="default_exam_duration",
            config_value="60",
            description="默认考试时长(分钟)",
            updated_at=datetime.now(),
        ),
        SystemConfig(
            config_key="default_pass_score_ratio",
            config_value="0.6",
            description="默认及格线比例",
            updated_at=datetime.now(),
        ),
        SystemConfig(
            config_key="enable_monitor",
            config_value="1",
            description="是否启用考试监控(0否1是)",
            updated_at=datetime.now(),
        ),
        SystemConfig(
            config_key="enable_auto_submit",
            config_value="1",
            description="是否启用到时自动提交(0否1是)",
            updated_at=datetime.now(),
        ),
    ]
    db.add_all(configs)
    db.commit()
    print("  [完成] 创建系统默认配置")


def _ensure_exam_notice_config(db: Session) -> None:
    """确保系统配置中有 exam_notice 键（全局考试注意事项）"""
    existing = db.query(SystemConfig).filter(SystemConfig.config_key == "exam_notice").first()
    if existing:
        print("  [跳过] exam_notice 配置已存在")
        return

    default_notice = (
        "1. 考试过程中请独立完成，禁止与他人交流或查阅任何资料。\n"
        "2. 禁止切换屏幕或打开其他程序，系统将自动记录切屏行为。\n"
        "3. 请确保网络连接稳定，答案会自动实时保存。\n"
        "4. 答题完毕后请仔细检查所有题目，确认无误后再提交。\n"
        "5. 提交后不可修改，请谨慎操作。"
    )
    config = SystemConfig(
        config_key="exam_notice",
        config_value=default_notice,
        description="考试注意事项（全局，考生登录后统一展示）",
        updated_at=datetime.now(),
    )
    db.add(config)
    db.commit()
    print("  [完成] 创建 exam_notice 默认配置")


def main() -> None:
    """初始化数据库并写入初始数据"""
    print("=" * 60)
    print("  学习培训考试管理系统 - 数据库初始化")
    print("=" * 60)

    # 1. 创建所有表
    print("\n[1/3] 创建数据库表...")
    try:
        init_db()
        print("  [完成] 所有数据表已创建")
    except Exception as e:
        print(f"  [错误] 创建数据表失败: {e}")
        sys.exit(1)

    # 2. 写入初始数据
    print("\n[2/3] 写入初始数据...")
    db = SessionLocal()
    try:
        seed_admin_user(db)
        seed_default_classes(db)
        seed_default_categories(db)
        seed_system_configs(db)
        _ensure_exam_notice_config(db)
    except Exception as e:
        db.rollback()
        print(f"  [错误] 写入初始数据失败: {e}")
        sys.exit(1)
    finally:
        db.close()

    # 3. 完成
    print("\n[3/3] 初始化完成!")
    print("=" * 60)
    print("  默认管理员: admin / admin123")
    print("  请及时修改默认密码!")
    print("=" * 60)


if __name__ == "__main__":
    main()
