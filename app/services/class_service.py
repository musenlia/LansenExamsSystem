# -*- coding: utf-8 -*-
"""班级服务 - CRUD"""

from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from models.class_ import Class
from models.user import User


class ClassService:
    """班级服务"""

    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        size: int = 20,
        keyword: Optional[str] = None,
    ) -> dict:
        """获取班级列表"""
        query = db.query(Class)

        if keyword:
            query = query.filter(Class.name.contains(keyword))

        total = query.count()
        items = query.order_by(Class.id.desc()).offset((page - 1) * size).limit(size).all()

        # 附加学生数量
        result_items = []
        for cls in items:
            cls_dict = cls.to_dict()
            student_count = db.query(User).filter(User.class_id == cls.id).count()
            cls_dict["student_count"] = student_count
            result_items.append(cls_dict)

        return {
            "items": result_items,
            "total": total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def get_all(db: Session) -> list:
        """获取所有班级（下拉选择用，含学生人数）"""
        classes = db.query(Class).order_by(Class.id).all()
        result = []
        for cls in classes:
            cls_dict = cls.to_dict()
            student_count = db.query(User).filter(User.class_id == cls.id).count()
            cls_dict["student_count"] = student_count
            result.append(cls_dict)
        return result

    @staticmethod
    def get_by_id(db: Session, class_id: int) -> Optional[Class]:
        """根据ID获取班级"""
        return db.query(Class).filter(Class.id == class_id).first()

    @staticmethod
    def create(db: Session, data: dict) -> Tuple[Optional[Class], str]:
        """创建班级"""
        existing = db.query(Class).filter(Class.name == data["name"]).first()
        if existing:
            return None, "班级名称已存在"

        cls = Class(
            name=data["name"],
            description=data.get("description"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(cls)
        db.commit()
        db.refresh(cls)
        return cls, "创建成功"

    @staticmethod
    def update(db: Session, class_id: int, data: dict) -> Tuple[Optional[Class], str]:
        """更新班级"""
        cls = db.query(Class).filter(Class.id == class_id).first()
        if not cls:
            return None, "班级不存在"

        if "name" in data and data["name"] is not None:
            existing = db.query(Class).filter(Class.name == data["name"], Class.id != class_id).first()
            if existing:
                return None, "班级名称已存在"
            cls.name = data["name"]
        if "description" in data and data["description"] is not None:
            cls.description = data["description"]

        cls.updated_at = datetime.now()
        db.commit()
        db.refresh(cls)
        return cls, "更新成功"

    @staticmethod
    def delete(db: Session, class_id: int) -> Tuple[bool, str]:
        """删除班级"""
        cls = db.query(Class).filter(Class.id == class_id).first()
        if not cls:
            return False, "班级不存在"

        # 检查是否有学生
        student_count = db.query(User).filter(User.class_id == class_id).count()
        if student_count > 0:
            return False, f"该班级下有 {student_count} 名学生，无法删除"

        db.delete(cls)
        db.commit()
        return True, "删除成功"

    @staticmethod
    def get_students(db: Session, class_id: int) -> list:
        """获取班级学生列表"""
        students = db.query(User).filter(User.class_id == class_id, User.role == "student").all()
        return [s.to_dict() for s in students]
