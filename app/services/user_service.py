# -*- coding: utf-8 -*-
"""用户服务 - CRUD、批量导入、重置密码"""

from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.user import User
from models.class_ import Class
from services.import_export_service import ImportExportService
from utils.security import get_password_hash


class UserService:
    """用户服务"""

    # 允许排序的字段白名单（防注入）
    SORT_FIELDS = {"id", "username", "name", "role", "created_at"}

    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        size: int = 20,
        keyword: Optional[str] = None,
        role: Optional[str] = None,
        class_id: Optional[int] = None,
        status: Optional[str] = None,
        sort_by: str = "id",
        sort_order: str = "desc",
    ) -> dict:
        """获取用户列表（分页+筛选+排序）"""
        query = db.query(User)

        if keyword:
            query = query.filter(
                or_(
                    User.username.contains(keyword),
                    User.name.contains(keyword),
                )
            )
        if role:
            query = query.filter(User.role == role)
        if class_id:
            query = query.filter(User.class_id == class_id)
        if status:
            query = query.filter(User.status == status)

        total = query.count()

        # 动态排序（白名单校验）
        if sort_by not in UserService.SORT_FIELDS:
            sort_by = "id"
        sort_col = getattr(User, sort_by)
        order_expr = sort_col.asc() if sort_order == "asc" else sort_col.desc()
        items = query.order_by(order_expr).offset((page - 1) * size).limit(size).all()

        # 附加班级名称
        result_items = []
        for user in items:
            user_dict = user.to_dict()
            if user.class_id:
                cls = db.query(Class).filter(Class.id == user.class_id).first()
                user_dict["class_name"] = cls.name if cls else None
            else:
                user_dict["class_name"] = None
            result_items.append(user_dict)

        return {
            "items": result_items,
            "total": total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create(db: Session, data: dict) -> Tuple[Optional[User], str]:
        """创建用户"""
        # 检查用户名唯一性
        existing = db.query(User).filter(User.username == data["username"]).first()
        if existing:
            return None, "用户名已存在"

        # 处理班级
        class_id = data.get("class_id")
        if not class_id and data.get("class_name"):
            cls = db.query(Class).filter(Class.name == data["class_name"]).first()
            if cls:
                class_id = cls.id

        user = User(
            username=data["username"],
            name=data["name"],
            password=get_password_hash(data.get("password", "123456")),
            role=data.get("role", "student"),
            class_id=class_id,
            status=data.get("status", "active"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, "创建成功"

    @staticmethod
    def update(db: Session, user_id: int, data: dict) -> Tuple[Optional[User], str]:
        """更新用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "用户不存在"

        if "name" in data and data["name"] is not None:
            user.name = data["name"]
        if "password" in data and data["password"] is not None:
            user.password = get_password_hash(data["password"])
        if "role" in data and data["role"] is not None:
            user.role = data["role"]
        if "class_id" in data and data["class_id"] is not None:
            user.class_id = data["class_id"]
        if "status" in data and data["status"] is not None:
            user.status = data["status"]

        user.updated_at = datetime.now()
        db.commit()
        db.refresh(user)
        return user, "更新成功"

    @staticmethod
    def delete(db: Session, user_id: int) -> Tuple[bool, str]:
        """删除用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"
        if user.role == "admin":
            admin_count = db.query(User).filter(User.role == "admin").count()
            if admin_count <= 1:
                return False, "不能删除最后一个管理员账号"

        db.delete(user)
        db.commit()
        return True, "删除成功"

    @staticmethod
    def batch_delete(db: Session, ids: list) -> dict:
        """批量删除用户"""
        success_count = 0
        fail_count = 0
        errors = []
        for user_id in ids:
            ok, msg = UserService.delete(db, user_id)
            if ok:
                success_count += 1
            else:
                fail_count += 1
                errors.append({"id": user_id, "reason": msg})
        return {"success_count": success_count, "fail_count": fail_count, "errors": errors}

    @staticmethod
    def batch_reset_password(db: Session, ids: list) -> dict:
        """批量重置密码"""
        success_count = 0
        fail_count = 0
        errors = []
        for user_id in ids:
            ok, msg = UserService.reset_password(db, user_id)
            if ok:
                success_count += 1
            else:
                fail_count += 1
                errors.append({"id": user_id, "reason": msg})
        return {"success_count": success_count, "fail_count": fail_count, "errors": errors}

    @staticmethod
    def batch_import(db: Session, file_data: bytes) -> dict:
        """批量导入用户"""
        return ImportExportService.import_users(db, file_data)

    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str = "123456") -> Tuple[bool, str]:
        """重置密码"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"
        user.password = get_password_hash(new_password)
        user.updated_at = datetime.now()
        db.commit()
        return True, f"密码已重置为: {new_password}"

    @staticmethod
    def get_user_with_class(db: Session, user: User) -> dict:
        """获取用户信息（含班级名称）"""
        user_dict = user.to_dict()
        if user.class_id:
            cls = db.query(Class).filter(Class.id == user.class_id).first()
            user_dict["class_name"] = cls.name if cls else None
        else:
            user_dict["class_name"] = None
        return user_dict
