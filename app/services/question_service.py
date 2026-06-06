# -*- coding: utf-8 -*-
"""题目服务 - CRUD、Excel导入导出、统计"""

from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.question import Question
from models.category import Category
from services.import_export_service import ImportExportService


class QuestionService:
    """题目服务"""

    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        size: int = 20,
        keyword: Optional[str] = None,
        type: Optional[str] = None,
        difficulty: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> dict:
        """获取题目列表"""
        query = db.query(Question)

        if keyword:
            query = query.filter(Question.content.contains(keyword))
        if type:
            query = query.filter(Question.type == type)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        if category_id is not None:
            # 包含子分类
            child_ids = _get_child_category_ids(db, category_id)
            category_ids = [category_id] + child_ids
            query = query.filter(Question.category_id.in_(category_ids))

        total = query.count()
        items = query.order_by(Question.id.desc()).offset((page - 1) * size).limit(size).all()

        result_items = []
        for q in items:
            q_dict = q.to_dict()
            if q.category_id:
                cat = db.query(Category).filter(Category.id == q.category_id).first()
                q_dict["category_name"] = cat.name if cat else None
            else:
                q_dict["category_name"] = None
            result_items.append(q_dict)

        return {
            "items": result_items,
            "total": total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def get_by_id(db: Session, question_id: int) -> Optional[Question]:
        """根据ID获取题目"""
        return db.query(Question).filter(Question.id == question_id).first()

    @staticmethod
    def create(db: Session, data: dict) -> Tuple[Optional[Question], str]:
        """创建题目"""
        question = Question(
            type=data["type"],
            content=data["content"],
            options=data.get("options"),
            answer=data["answer"],
            fill_match_mode=data.get("fill_match_mode"),
            analysis=data.get("analysis"),
            score=data.get("score", 2),
            difficulty=data.get("difficulty", "medium"),
            category_id=data.get("category_id"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question, "创建成功"

    @staticmethod
    def update(db: Session, question_id: int, data: dict) -> Tuple[Optional[Question], str]:
        """更新题目"""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return None, "题目不存在"

        for field in ["type", "content", "options", "answer", "fill_match_mode",
                       "analysis", "score", "difficulty", "category_id"]:
            if field in data and data[field] is not None:
                setattr(question, field, data[field])

        question.updated_at = datetime.now()
        db.commit()
        db.refresh(question)
        return question, "更新成功"

    @staticmethod
    def delete(db: Session, question_id: int) -> Tuple[bool, str]:
        """删除题目"""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False, "题目不存在"

        # 检查是否被考试引用
        from models.exam import ExamQuestion
        ref_count = db.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).count()
        if ref_count > 0:
            return False, f"该题目已被 {ref_count} 场考试引用，无法删除"

        db.delete(question)
        db.commit()
        return True, "删除成功"

    @staticmethod
    def batch_import(db: Session, file_data: bytes) -> dict:
        """批量导入题目"""
        return ImportExportService.import_questions(db, file_data)

    @staticmethod
    def get_stats(db: Session) -> dict:
        """获取题目统计"""
        total = db.query(Question).count()
        single_count = db.query(Question).filter(Question.type == "single").count()
        multiple_count = db.query(Question).filter(Question.type == "multiple").count()
        judge_count = db.query(Question).filter(Question.type == "judge").count()
        fill_count = db.query(Question).filter(Question.type == "fill").count()
        easy_count = db.query(Question).filter(Question.difficulty == "easy").count()
        medium_count = db.query(Question).filter(Question.difficulty == "medium").count()
        hard_count = db.query(Question).filter(Question.difficulty == "hard").count()

        return {
            "total": total,
            "single_count": single_count,
            "multiple_count": multiple_count,
            "judge_count": judge_count,
            "fill_count": fill_count,
            "easy_count": easy_count,
            "medium_count": medium_count,
            "hard_count": hard_count,
        }


def _get_child_category_ids(db: Session, parent_id: int) -> list:
    """递归获取所有子分类ID"""
    ids = []
    children = db.query(Category).filter(Category.parent_id == parent_id).all()
    for child in children:
        ids.append(child.id)
        ids.extend(_get_child_category_ids(db, child.id))
    return ids
