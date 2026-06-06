# -*- coding: utf-8 -*-
"""系统服务 - 系统配置CRUD、操作日志查询、考试数据备份与导入、系统重置、基础数据导出、仪表盘数据"""

import os
import json
import shutil
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from models.system_config import SystemConfig
from models.operation_log import OperationLog
from models.user import User
from models.class_ import Class
from models.question import Question
from models.category import Category
from models.exam import Exam, ExamQuestion, ExamClass
from models.session import ExamSession
from models.answer import Answer
from models.monitor_log import MonitorLog


class SystemService:
    """系统服务"""

    @staticmethod
    def get_configs(db: Session) -> list:
        """获取所有系统配置"""
        configs = db.query(SystemConfig).order_by(SystemConfig.id).all()
        return [c.to_dict() for c in configs]

    @staticmethod
    def get_config(db: Session, config_key: str) -> Optional[SystemConfig]:
        """获取单个配置"""
        return db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()

    @staticmethod
    def update_config(db: Session, config_key: str, config_value: str, description: str = None) -> Tuple[Optional[SystemConfig], str]:
        """更新系统配置"""
        config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
        if not config:
            # 创建新配置
            config = SystemConfig(
                config_key=config_key,
                config_value=config_value,
                description=description,
                updated_at=datetime.now(),
            )
            db.add(config)
        else:
            config.config_value = config_value
            if description:
                config.description = description
            config.updated_at = datetime.now()

        db.commit()
        db.refresh(config)
        return config, "更新成功"

    @staticmethod
    def get_operation_logs(
        db: Session,
        page: int = 1,
        size: int = 20,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """获取操作日志"""
        query = db.query(OperationLog)

        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        if action:
            query = query.filter(OperationLog.action.contains(action))
        if start_date:
            query = query.filter(OperationLog.created_at >= start_date)
        if end_date:
            query = query.filter(OperationLog.created_at <= end_date + " 23:59:59")

        total = query.count()
        logs = query.order_by(OperationLog.id.desc()).offset((page - 1) * size).limit(size).all()

        items = []
        for log in logs:
            log_dict = log.to_dict()
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                log_dict["username"] = user.username if user else None
            items.append(log_dict)

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def log_operation(
        db: Session,
        user_id: Optional[int],
        action: str,
        target_type: str = None,
        target_id: int = None,
        detail: str = None,
        ip_address: str = None,
    ) -> None:
        """记录操作日志"""
        log = OperationLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address,
            created_at=datetime.now(),
        )
        db.add(log)
        db.commit()

    # ============================================================
    # 考试数据备份与导入
    # ============================================================

    BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backups")

    @staticmethod
    def _ensure_backup_dir() -> str:
        """确保备份目录存在并返回路径"""
        backup_dir = SystemService.BACKUP_DIR
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @staticmethod
    def export_exam_backup(db: Session, exam_ids: List[int]) -> Tuple[str, str]:
        """
        按考试导出备份 JSON 文件。
        返回 (文件路径, 文件名)。
        包含：考试信息、题目、所有考生的成绩与答卷详情。
        """
        backup_dir = SystemService._ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exam_backup_{timestamp}.xlsx"
        filepath = os.path.join(backup_dir, filename)

        backup_data = {
            "version": "2.0",
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system": "学习培训考试管理系统",
            "exams": [],
        }

        for exam_id in exam_ids:
            exam = db.query(Exam).filter(Exam.id == exam_id).first()
            if not exam:
                continue

            # 考试基本信息
            exam_info = exam.to_dict()

            # 关联班级
            exam_classes = db.query(ExamClass).filter(ExamClass.exam_id == exam_id).all()
            class_list = []
            for ec in exam_classes:
                cls = db.query(Class).filter(Class.id == ec.class_id).first()
                if cls:
                    class_list.append({"id": cls.id, "name": cls.name})
            exam_info["classes"] = class_list

            # 考试题目（含完整题目信息）
            eqs = db.query(ExamQuestion).filter(
                ExamQuestion.exam_id == exam_id
            ).order_by(ExamQuestion.order_num).all()
            question_list = []
            for eq in eqs:
                q = db.query(Question).filter(Question.id == eq.question_id).first()
                if q:
                    q_dict = q.to_dict()
                    q_dict["exam_score"] = eq.score  # 该题在本次考试中的分值
                    q_dict["order_num"] = eq.order_num
                    question_list.append(q_dict)
            exam_info["questions"] = question_list

            # 收集本次考试涉及的所有分类
            category_ids = set()
            for q_dict in question_list:
                if q_dict.get("category_id"):
                    category_ids.add(q_dict["category_id"])
            category_list = []
            if category_ids:
                categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
                for cat in categories:
                    category_list.append({
                        "id": cat.id,
                        "name": cat.name,
                        "parent_id": cat.parent_id,
                        "sort_order": cat.sort_order,
                    })
            exam_info["categories"] = category_list

            # 所有考生会话与答卷
            sessions = db.query(ExamSession).filter(ExamSession.exam_id == exam_id).all()
            student_results = []
            for sess in sessions:
                user = db.query(User).filter(User.id == sess.user_id).first()
                class_name = None
                if user and user.class_id:
                    cls = db.query(Class).filter(Class.id == user.class_id).first()
                    class_name = cls.name if cls else None

                # 答卷详情
                answers = db.query(Answer).filter(Answer.session_id == sess.id).all()
                answer_details = []
                for ans in answers:
                    q = db.query(Question).filter(Question.id == ans.question_id).first()
                    if q:
                        options = q.options
                        if options and isinstance(options, dict):
                            options = [{"label": k, "content": v} for k, v in options.items()]
                        answer_details.append({
                            "question_id": q.id,
                            "type": q.type,
                            "content": q.content,
                            "options": options,
                            "correct_answer": q.answer,
                            "student_answer": ans.user_answer,
                            "score": ans.score,
                            "max_score": q.score,
                            "is_correct": bool(ans.is_correct) if ans.is_correct is not None else None,
                            "analysis": q.analysis,
                        })

                student_results.append({
                    "session_id": sess.id,
                    "username": user.username if user else "",
                    "name": user.name if user else "",
                    "class_name": class_name,
                    "status": sess.status,
                    "score": sess.total_score,
                    "pass_score": exam.pass_score,
                    "is_passed": bool(sess.total_score >= exam.pass_score) if (sess.total_score is not None) else None,
                    "duration_seconds": sess.time_used or 0,
                    "start_time": sess.start_time.isoformat() if sess.start_time else None,
                    "submit_time": sess.submit_time.isoformat() if sess.submit_time else None,
                    "answers": answer_details,
                })
            exam_info["student_results"] = student_results

            backup_data["exams"].append(exam_info)

        if not backup_data["exams"]:
            return None, "未找到有效的考试数据"

        # 写入 Excel（多Sheet：信息/题目/成绩/答卷 + 隐藏JSON Sheet）
        from utils.excel_helper import export_exam_backup_to_excel
        excel_bytes = export_exam_backup_to_excel(backup_data)
        with open(filepath, "wb") as f:
            f.write(excel_bytes)

        return filepath, filename

    @staticmethod
    def list_backups() -> List[dict]:
        """列出备份文件"""
        backup_dir = SystemService._ensure_backup_dir()
        files = []
        if os.path.exists(backup_dir):
            for fname in sorted(os.listdir(backup_dir), reverse=True):
                if fname.endswith(".json") or fname.endswith(".xlsx"):
                    fpath = os.path.join(backup_dir, fname)
                    stat = os.stat(fpath)
                    files.append({
                        "filename": fname,
                        "size": stat.st_size,
                        "size_text": _format_file_size(stat.st_size),
                        "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    })
        return files

    @staticmethod
    def get_backup_filepath(filename: str) -> Optional[str]:
        """获取备份文件的完整路径（安全检查）"""
        backup_dir = SystemService._ensure_backup_dir()
        # 安全：防止路径穿越，只允许 json 和 xlsx 文件
        safe_name = os.path.basename(filename)
        if not (safe_name.endswith(".json") or safe_name.endswith(".xlsx")):
            return None
        filepath = os.path.join(backup_dir, safe_name)
        if os.path.exists(filepath):
            return filepath
        return None

    @staticmethod
    def delete_backup(filename: str) -> Tuple[bool, str]:
        """删除备份文件"""
        filepath = SystemService.get_backup_filepath(filename)
        if not filepath:
            return False, "备份文件不存在"
        try:
            os.remove(filepath)
            return True, "删除成功"
        except Exception as e:
            return False, f"删除失败: {str(e)}"

    @staticmethod
    def import_exam_backup(file_content: bytes, filename: str) -> Tuple[bool, str, dict]:
        """
        导入考试备份文件（只读解析，返回摘要信息）。
        支持 xlsx（多Sheet格式）和 json 格式。
        导入为只读模式：解析返回考试和考生数据摘要供前端展示复盘。
        返回 (success, message, parsed_data)
        """
        # 根据文件名后缀选择解析方式
        if filename.endswith(".xlsx"):
            from utils.excel_helper import read_exam_backup_from_excel
            ok, msg, data = read_exam_backup_from_excel(file_content)
            if not ok:
                return False, msg, {}
        else:
            try:
                data = json.loads(file_content.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return False, "文件格式错误，请选择有效的备份文件", {}

        # 验证基本结构
        if not isinstance(data, dict) or "exams" not in data:
            # 检查是否为基础数据备份（用户/题库）
            backup_type = data.get("type", "") if isinstance(data, dict) else ""
            type_hints = {
                "users_backup": "用户与班级备份数据，不支持复盘功能，请直接下载查看",
                "questions_backup": "题库备份数据，不支持复盘功能，请直接下载查看",
            }
            hint = type_hints.get(backup_type, "备份文件格式不正确，缺少 exams 字段")
            return False, hint, {}

        exams = data.get("exams", [])
        if not exams:
            return False, "备份文件中没有考试数据", {}

        summary = {
            "export_time": data.get("export_time", "未知"),
            "system": data.get("system", "未知"),
            "exam_count": len(exams),
            "exams": [],
        }

        for exam in exams:
            exam_name = exam.get("name", "未知考试")
            students = exam.get("student_results", [])
            questions = exam.get("questions", [])

            # 统计成绩
            scores = [s["score"] for s in students if s.get("score") is not None]
            avg_score = round(sum(scores) / len(scores), 1) if scores else None
            max_score = max(scores) if scores else None
            min_score = min(scores) if scores else None
            pass_count = sum(1 for s in students if s.get("is_passed"))
            pass_rate = round(pass_count / len(students) * 100, 1) if students else None

            summary["exams"].append({
                "name": exam_name,
                "student_count": len(students),
                "question_count": len(questions),
                "avg_score": avg_score,
                "max_score": max_score,
                "min_score": min_score,
                "pass_count": pass_count,
                "pass_rate": pass_rate,
            })

        return True, "解析成功", summary

    @staticmethod
    def restore_exam_backup(db: Session, file_content: bytes, filename: str) -> Tuple[bool, str, dict]:
        """
        恢复考试备份数据到数据库。
        支持 xlsx（多Sheet格式）和 json 格式。
        将考试、题目、考生成绩和答卷恢复到系统中。
        返回 (success, message, result_data)
        """
        # 根据文件名后缀选择解析方式
        if filename.endswith(".xlsx"):
            from utils.excel_helper import read_exam_backup_from_excel
            ok, msg, data = read_exam_backup_from_excel(file_content)
            if not ok:
                return False, msg, {}
        else:
            try:
                data = json.loads(file_content.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return False, "文件格式错误，请选择有效的备份文件", {}

        if not isinstance(data, dict) or "exams" not in data:
            return False, "备份文件格式不正确，缺少 exams 字段", {}

        exams = data.get("exams", [])
        if not exams:
            return False, "备份文件中没有考试数据", {}

        restored_exams = []  # 恢复成功的考试 {id, name, student_count}

        try:
            for exam_data in exams:
                exam_name = exam_data.get("name", "未知考试")

                # 1. 创建考试记录（状态设为 ended，因为是历史数据复盘）
                exam = Exam(
                    name=f"{exam_name}（复盘恢复）",
                    description=exam_data.get("description"),
                    start_time=_parse_datetime(exam_data.get("start_time")),
                    duration=exam_data.get("duration", 60),
                    total_score=exam_data.get("total_score", 100),
                    pass_score=exam_data.get("pass_score", 60),
                    mode=exam_data.get("mode", "fixed"),
                    status="ended",
                    shuffle_question=1 if exam_data.get("shuffle_question") else 0,
                    shuffle_option=1 if exam_data.get("shuffle_option") else 0,
                    allow_early_submit=1 if exam_data.get("allow_early_submit", True) else 0,
                    random_config=exam_data.get("random_config"),
                    notice=exam_data.get("notice"),
                    created_by=None,
                )
                db.add(exam)
                db.flush()  # 获取 exam.id

                # 1.5 恢复缺失的分类（确保题目能正确关联）
                backup_categories = exam_data.get("categories", [])
                for cat_data in backup_categories:
                    cat_name = cat_data.get("name", "")
                    if not cat_name:
                        continue
                    # 按名称查找或创建分类
                    existing_cat = db.query(Category).filter(Category.name == cat_name).first()
                    if not existing_cat:
                        cat = Category(
                            name=cat_name,
                            parent_id=cat_data.get("parent_id"),
                            sort_order=cat_data.get("sort_order", 0),
                            created_at=_parse_datetime(cat_data.get("created_at")) or datetime.now(),
                            updated_at=_parse_datetime(cat_data.get("updated_at")) or datetime.now(),
                        )
                        db.add(cat)
                        db.flush()

                # 2. 恢复题目并关联考试
                backup_questions = exam_data.get("questions", [])
                question_id_map = {}  # backup_question_id -> new_question_id
                for idx, q_data in enumerate(backup_questions):
                    # 检查题库中是否已存在相同内容的题目
                    existing_q = db.query(Question).filter(
                        Question.content == q_data.get("content"),
                        Question.type == q_data.get("type"),
                    ).first()

                    if existing_q:
                        new_q_id = existing_q.id
                    else:
                        # 创建新题目
                        options = q_data.get("options")
                        # 统一 options 格式为 list
                        if options and isinstance(options, dict):
                            options = [{"label": k, "content": v} for k, v in options.items()]
                        elif not options:
                            options = None

                        # 验证 category_id 是否存在，不存在则置空
                        cat_id = q_data.get("category_id")
                        if cat_id:
                            cat_exists = db.query(Category.id).filter(Category.id == cat_id).first()
                            if not cat_exists:
                                cat_id = None

                        q = Question(
                            content=q_data.get("content"),
                            type=q_data.get("type", "single"),
                            options=options,
                            answer=q_data.get("answer"),
                            analysis=q_data.get("analysis"),
                            score=q_data.get("score", 2),
                            difficulty=q_data.get("difficulty", "medium"),
                            category_id=cat_id,
                            fill_match_mode=q_data.get("fill_match_mode"),
                        )
                        db.add(q)
                        db.flush()
                        new_q_id = q.id

                    backup_q_id = q_data.get("id")
                    if backup_q_id:
                        question_id_map[backup_q_id] = new_q_id

                    # 关联考试-题目（防重复）
                    existing_eq = db.query(ExamQuestion).filter(
                        ExamQuestion.exam_id == exam.id,
                        ExamQuestion.question_id == new_q_id,
                    ).first()
                    if not existing_eq:
                        eq = ExamQuestion(
                            exam_id=exam.id,
                            question_id=new_q_id,
                            order_num=idx + 1,
                            score=q_data.get("exam_score", q_data.get("score", 2)),
                        )
                        db.add(eq)

                # 3. 恢复考生答卷
                student_results = exam_data.get("student_results", [])
                restored_students = 0

                for sr in student_results:
                    username = sr.get("username", "")
                    name = sr.get("name", "")

                    # 查找或创建考生用户
                    user = db.query(User).filter(User.username == username).first()
                    if not user and username:
                        # 创建考生账号（密码设为默认 123456）
                        user = User(
                            username=username,
                            name=name,
                            password="$2b$12$LJ3m9ys3z.FH5Y1x9JnzvuQPB8ZQh2B8i9N7kJh6fVfE4k7pX9W.G",  # bcrypt(123456)
                            role="student",
                        )
                        # 尝试关联班级
                        class_name = sr.get("class_name")
                        if class_name:
                            cls = db.query(Class).filter(Class.name == class_name).first()
                            if cls:
                                user.class_id = cls.id
                        db.add(user)
                        db.flush()

                    if not user:
                        continue

                    # 检查是否已有该考生的会话
                    existing_session = db.query(ExamSession).filter(
                        ExamSession.exam_id == exam.id,
                        ExamSession.user_id == user.id,
                    ).first()

                    if existing_session:
                        continue  # 跳过已存在的会话

                    # 创建考试会话
                    session = ExamSession(
                        exam_id=exam.id,
                        user_id=user.id,
                        status=sr.get("status", "submitted"),
                        total_score=sr.get("score"),
                        time_used=sr.get("duration_seconds"),
                        start_time=_parse_datetime(sr.get("start_time")),
                        submit_time=_parse_datetime(sr.get("submit_time")),
                        is_active=0,  # 历史数据不活跃
                    )
                    db.add(session)
                    db.flush()

                    # 恢复答卷详情
                    answers = sr.get("answers", [])
                    for ans_data in answers:
                        backup_q_id = ans_data.get("question_id")
                        new_q_id = question_id_map.get(backup_q_id)
                        if not new_q_id:
                            continue

                        answer = Answer(
                            session_id=session.id,
                            question_id=new_q_id,
                            user_answer=ans_data.get("student_answer"),
                            score=ans_data.get("score"),
                            is_correct=1 if ans_data.get("is_correct") else (0 if ans_data.get("is_correct") is False else None),
                            answered_at=_parse_datetime(sr.get("submit_time")),
                        )
                        db.add(answer)

                    restored_students += 1

                restored_exams.append({
                    "id": exam.id,
                    "name": exam.name,
                    "student_count": restored_students,
                })

            db.commit()
            return True, f"成功恢复 {len(restored_exams)} 场考试数据", {
                "exam_count": len(restored_exams),
                "exams": restored_exams,
            }
        except Exception as e:
            db.rollback()
            return False, f"恢复失败: {str(e)}", {}

    # ============================================================
    # 系统重置
    # ============================================================

    @staticmethod
    def reset_system(db: Session) -> Tuple[bool, str]:
        """
        重置系统到初始状态：清空所有业务数据，重新写入默认数据。
        按外键依赖顺序删除：answers → monitor_logs → sessions → exam_questions → exam_classes → exams
        → questions → categories → operation_logs → system_configs → users → classes
        """
        try:
            # 按外键依赖顺序清空所有表
            tables_to_clear = [
                Answer, MonitorLog, ExamSession,
                ExamQuestion, ExamClass, Exam,
                Question, Category,
                OperationLog, SystemConfig,
                User, Class,
            ]
            cleared = []
            for model in tables_to_clear:
                count = db.query(model).count()
                if count > 0:
                    db.query(model).delete()
                    cleared.append(f"{model.__tablename__}({count}条)")
                else:
                    cleared.append(f"{model.__tablename__}(0条)")

            db.commit()

            # 重新写入初始数据（复用 init_data 的 seed 函数）
            from init_data import (
                seed_admin_user, seed_default_classes,
                seed_default_categories, seed_system_configs,
                _ensure_exam_notice_config,
            )
            seed_admin_user(db)
            seed_default_classes(db)
            seed_default_categories(db)
            seed_system_configs(db)
            _ensure_exam_notice_config(db)

            return True, f"系统重置成功，已清空并重新初始化: {', '.join(cleared)}"
        except Exception as e:
            db.rollback()
            return False, f"系统重置失败: {str(e)}"

    # ============================================================
    # 基础数据导出
    # ============================================================

    @staticmethod
    def export_users_backup(db: Session) -> Tuple[str, str]:
        """导出用户+班级数据到 Excel 文件（与导入模板格式一致，可直接重新导入）"""
        from utils.excel_helper import export_users_to_excel

        backup_dir = SystemService._ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"users_backup_{timestamp}.xlsx"
        filepath = os.path.join(backup_dir, filename)

        users = db.query(User).order_by(User.id).all()
        users_data = []
        for u in users:
            class_name = None
            if u.class_id:
                cls = db.query(Class).filter(Class.id == u.class_id).first()
                class_name = cls.name if cls else None
            users_data.append({
                "username": u.username,
                "name": u.name,
                "role": u.role,
                "class_name": class_name or "",
            })

        excel_bytes = export_users_to_excel(users_data)
        with open(filepath, "wb") as f:
            f.write(excel_bytes)

        return filepath, filename

    @staticmethod
    def export_questions_backup(db: Session) -> Tuple[str, str]:
        """导出题库（分类+题目）数据到 Excel 文件（与导入模板格式一致，可直接重新导入）"""
        from utils.excel_helper import export_questions_to_excel

        backup_dir = SystemService._ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"questions_backup_{timestamp}.xlsx"
        filepath = os.path.join(backup_dir, filename)

        questions = db.query(Question).order_by(Question.id).all()
        questions_data = []
        for q in questions:
            # 获取分类名
            category_name = ""
            if q.category_id:
                cat = db.query(Category).filter(Category.id == q.category_id).first()
                category_name = cat.name if cat else ""
            questions_data.append({
                "type": q.type,
                "content": q.content,
                "options": q.options,
                "answer": q.answer,
                "score": q.score,
                "difficulty": q.difficulty,
                "category_name": category_name,
                "analysis": q.analysis or "",
                "fill_match_mode": q.fill_match_mode or "",
            })

        excel_bytes = export_questions_to_excel(questions_data)
        with open(filepath, "wb") as f:
            f.write(excel_bytes)

        return filepath, filename

    @staticmethod
    def get_dashboard(db: Session) -> dict:
        """获取仪表盘数据"""
        total_questions = db.query(Question).count()
        total_students = db.query(User).filter(User.role == "student").count()
        total_exams = db.query(Exam).count()

        # 今日考试
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        today_exams = db.query(Exam).filter(
            Exam.start_time >= today_start,
            Exam.start_time <= today_end,
        ).count()

        # 进行中的考试（status=ongoing 或 status=published且无开始时间）
        ongoing_exams_list = db.query(Exam).filter(
            (Exam.status == "ongoing") | 
            (Exam.status == "published") & (Exam.start_time == None)
        ).all()
        ongoing_list = []
        for exam in ongoing_exams_list:
            participant_count = db.query(ExamSession).filter(ExamSession.exam_id == exam.id).count()
            submitted_count = db.query(ExamSession).filter(
                ExamSession.exam_id == exam.id,
                ExamSession.status == "submitted",
            ).count()
            # Exam 没有 end_time 字段，用 start_time + duration 计算
            end_time = None
            if exam.start_time and exam.duration:
                from datetime import timedelta
                end_time = (exam.start_time + timedelta(minutes=exam.duration)).isoformat()
            ongoing_list.append({
                "id": exam.id,
                "title": exam.name,
                "start_time": exam.start_time.isoformat() if exam.start_time else None,
                "end_time": end_time,
                "participant_count": participant_count,
                "submitted_count": submitted_count,
            })

        # 即将开始的考试（status=published 且 start_time 在未来）
        upcoming_exams_list = db.query(Exam).filter(
            Exam.status == "published",
            Exam.start_time > datetime.now(),
        ).order_by(Exam.start_time.asc()).limit(5).all()
        upcoming_list = []
        for exam in upcoming_exams_list:
            participant_count = db.query(ExamSession).filter(ExamSession.exam_id == exam.id).count()
            end_time = None
            if exam.start_time and exam.duration:
                from datetime import timedelta
                end_time = (exam.start_time + timedelta(minutes=exam.duration)).isoformat()
            upcoming_list.append({
                "id": exam.id,
                "title": exam.name,
                "start_time": exam.start_time.isoformat() if exam.start_time else None,
                "end_time": end_time,
                "participant_count": participant_count,
            })

        return {
            "total_questions": total_questions,
            "total_students": total_students,
            "total_exams": total_exams,
            "today_exams": today_exams,
            "ongoing_exams": ongoing_list,
            "upcoming_exams": upcoming_list,
        }


def _format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _parse_datetime(dt_str: str | None) -> datetime | None:
    """解析 ISO 格式时间字符串为 datetime 对象"""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None
