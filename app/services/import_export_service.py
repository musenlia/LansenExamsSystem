# -*- coding: utf-8 -*-
"""导入导出服务 - Excel 模板定义、用户/题目导入、成绩导出"""

from datetime import datetime
from typing import Tuple
from sqlalchemy.orm import Session

from models.user import User
from models.class_ import Class
from models.question import Question
from models.category import Category
from utils.excel_helper import (
    create_user_import_template,
    parse_user_import,
    create_question_import_template,
    parse_question_import,
)


class ImportExportService:
    """导入导出服务"""

    @staticmethod
    def get_user_template() -> bytes:
        """获取用户导入模板"""
        return create_user_import_template()

    @staticmethod
    def import_users(db: Session, file_data: bytes) -> dict:
        """
        批量导入用户

        Returns:
            {"success_count": N, "fail_count": N, "errors": [...]}
        """
        success_data, parse_errors = parse_user_import(file_data)

        if parse_errors and not success_data:
            return {
                "success_count": 0,
                "fail_count": 0,
                "errors": parse_errors,
            }

        success_count = 0
        errors = list(parse_errors)

        for row_data in success_data:
            try:
                # 检查用户名唯一性
                existing = db.query(User).filter(User.username == row_data["username"]).first()
                if existing:
                    errors.append(f"用户名 {row_data['username']} 已存在")
                    continue

                # 处理班级
                class_id = None
                if row_data.get("class_name"):
                    cls = db.query(Class).filter(Class.name == row_data["class_name"]).first()
                    if cls:
                        class_id = cls.id
                    else:
                        # 自动创建班级
                        cls = Class(
                            name=row_data["class_name"],
                            description="导入时自动创建",
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                        )
                        db.add(cls)
                        db.flush()
                        class_id = cls.id

                user = User(
                    username=row_data["username"],
                    name=row_data["name"],
                    password=row_data["password"],
                    role=row_data.get("role", "student"),
                    class_id=class_id,
                    status="active",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(user)
                success_count += 1
            except Exception as e:
                errors.append(f"导入用户 {row_data.get('username', '')} 失败: {str(e)}")

        db.commit()
        return {
            "success_count": success_count,
            "fail_count": len(errors) - len(parse_errors),
            "errors": errors,
        }

    @staticmethod
    def get_question_template() -> bytes:
        """获取题目导入模板"""
        return create_question_import_template()

    @staticmethod
    def import_questions(db: Session, file_data: bytes) -> dict:
        """
        批量导入题目

        Returns:
            {"success_count": N, "fail_count": N, "errors": [...]}
        """
        success_data, parse_errors = parse_question_import(file_data)

        if parse_errors and not success_data:
            return {
                "success_count": 0,
                "fail_count": 0,
                "errors": parse_errors,
            }

        success_count = 0
        errors = list(parse_errors)

        for row_data in success_data:
            try:
                # 处理分类
                category_id = None
                if row_data.get("category_name"):
                    cat = db.query(Category).filter(Category.name == row_data["category_name"]).first()
                    if cat:
                        category_id = cat.id
                    else:
                        # 自动创建分类
                        cat = Category(
                            name=row_data["category_name"],
                            description="导入时自动创建",
                            sort_order=99,
                            created_at=datetime.now(),
                        )
                        db.add(cat)
                        db.flush()
                        category_id = cat.id

                # 验证难度
                difficulty = row_data.get("difficulty", "medium")
                if difficulty not in ("easy", "medium", "hard"):
                    difficulty = "medium"

                question = Question(
                    type=row_data["type"],
                    content=row_data["content"],
                    options=row_data.get("options"),
                    answer=row_data["answer"],
                    fill_match_mode=row_data.get("fill_match_mode"),
                    analysis=row_data.get("analysis"),
                    score=row_data.get("score", 2),
                    difficulty=difficulty,
                    category_id=category_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(question)
                success_count += 1
            except Exception as e:
                errors.append(f"导入题目失败（内容: {row_data.get('content', '')[:20]}...）: {str(e)}")

        db.commit()
        return {
            "success_count": success_count,
            "fail_count": len(errors) - len(parse_errors),
            "errors": errors,
        }
