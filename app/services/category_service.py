# -*- coding: utf-8 -*-
"""分类服务 - 树形CRUD"""

from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from models.category import Category
from models.question import Question


class CategoryService:
    """分类服务"""

    @staticmethod
    def get_tree(db: Session) -> List[dict]:
        """获取分类树"""
        categories = db.query(Category).order_by(Category.sort_order, Category.id).all()

        # 统计每个分类的题目数量
        question_counts = {}
        for cat in categories:
            count = db.query(Question).filter(Question.category_id == cat.id).count()
            question_counts[cat.id] = count

        # 构建树
        cat_map = {}
        for cat in categories:
            cat_dict = cat.to_dict()
            cat_dict["question_count"] = question_counts.get(cat.id, 0)
            cat_dict["children"] = []
            cat_map[cat.id] = cat_dict

        tree = []
        for cat in categories:
            node = cat_map[cat.id]
            if cat.parent_id and cat.parent_id in cat_map:
                cat_map[cat.parent_id]["children"].append(node)
            else:
                tree.append(node)

        return tree

    @staticmethod
    def get_list(db: Session) -> List[dict]:
        """获取扁平分类列表"""
        categories = db.query(Category).order_by(Category.sort_order, Category.id).all()
        result = []
        for cat in categories:
            cat_dict = cat.to_dict()
            count = db.query(Question).filter(Question.category_id == cat.id).count()
            cat_dict["question_count"] = count
            result.append(cat_dict)
        return result

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[Category]:
        """根据ID获取分类"""
        return db.query(Category).filter(Category.id == category_id).first()

    @staticmethod
    def create(db: Session, data: dict) -> Tuple[Optional[Category], str]:
        """创建分类"""
        # 检查同级同名
        existing = db.query(Category).filter(
            Category.name == data["name"],
            Category.parent_id == data.get("parent_id"),
        ).first()
        if existing:
            return None, "同级下已存在相同名称的分类"

        category = Category(
            name=data["name"],
            parent_id=data.get("parent_id"),
            description=data.get("description"),
            sort_order=data.get("sort_order", 0),
            created_at=datetime.now(),
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category, "创建成功"

    @staticmethod
    def update(db: Session, category_id: int, data: dict) -> Tuple[Optional[Category], str]:
        """更新分类"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return None, "分类不存在"

        # 防止循环引用
        if "parent_id" in data and data["parent_id"] is not None:
            if data["parent_id"] == category_id:
                return None, "不能将自身设为父分类"
            # 检查是否会形成循环
            parent_id = data["parent_id"]
            visited = {category_id}
            while parent_id:
                if parent_id in visited:
                    return None, "不能形成循环引用"
                visited.add(parent_id)
                parent = db.query(Category).filter(Category.id == parent_id).first()
                if parent:
                    parent_id = parent.parent_id
                else:
                    break

        if "name" in data and data["name"] is not None:
            category.name = data["name"]
        if "parent_id" in data:
            category.parent_id = data["parent_id"]
        if "description" in data and data["description"] is not None:
            category.description = data["description"]
        if "sort_order" in data and data["sort_order"] is not None:
            category.sort_order = data["sort_order"]

        db.commit()
        db.refresh(category)
        return category, "更新成功"

    @staticmethod
    def delete(db: Session, category_id: int) -> Tuple[bool, str]:
        """删除分类"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return False, "分类不存在"

        # 检查子分类
        children = db.query(Category).filter(Category.parent_id == category_id).count()
        if children > 0:
            return False, "该分类下有子分类，无法删除"

        # 检查关联题目
        question_count = db.query(Question).filter(Question.category_id == category_id).count()
        if question_count > 0:
            return False, f"该分类下有 {question_count} 道题目，无法删除"

        db.delete(category)
        db.commit()
        return True, "删除成功"
