# -*- coding: utf-8 -*-
"""考试服务 - CRUD、组卷、状态流转"""

from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.exam import Exam, ExamQuestion, ExamClass
from models.question import Question
from models.session import ExamSession
from models.answer import Answer
from models.class_ import Class
from models.user import User


class ExamService:
    """考试服务"""

    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> dict:
        """获取考试列表"""
        query = db.query(Exam)

        if keyword:
            query = query.filter(Exam.name.contains(keyword))
        if status:
            query = query.filter(Exam.status == status)
        if mode:
            query = query.filter(Exam.mode == mode)

        total = query.count()
        items = query.order_by(Exam.id.desc()).offset((page - 1) * size).limit(size).all()

        result_items = []
        for exam in items:
            exam_dict = exam.to_dict()
            # 附加班级名称
            exam_classes = db.query(ExamClass).filter(ExamClass.exam_id == exam.id).all()
            class_ids = [ec.class_id for ec in exam_classes]
            class_names = []
            for cid in class_ids:
                cls = db.query(Class).filter(Class.id == cid).first()
                if cls:
                    class_names.append(cls.name)
            exam_dict["class_ids"] = class_ids
            exam_dict["class_names"] = class_names
            # 附加题目数量
            q_count = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam.id).count()
            exam_dict["question_count"] = q_count
            result_items.append(exam_dict)

        return {
            "items": result_items,
            "total": total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def get_by_id(db: Session, exam_id: int) -> Optional[Exam]:
        """根据ID获取考试"""
        return db.query(Exam).filter(Exam.id == exam_id).first()

    @staticmethod
    def get_detail(db: Session, exam_id: int) -> Optional[dict]:
        """获取考试详情（含题目和班级）"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        exam_dict = exam.to_dict()

        # 班级列表
        exam_classes = db.query(ExamClass).filter(ExamClass.exam_id == exam_id).all()
        classes = []
        for ec in exam_classes:
            cls = db.query(Class).filter(Class.id == ec.class_id).first()
            if cls:
                classes.append({"id": cls.id, "name": cls.name})
        exam_dict["classes"] = classes

        # 题目列表
        exam_questions = (
            db.query(ExamQuestion)
            .filter(ExamQuestion.exam_id == exam_id)
            .order_by(ExamQuestion.order_num)
            .all()
        )
        questions = []
        for eq in exam_questions:
            q = db.query(Question).filter(Question.id == eq.question_id).first()
            if q:
                q_dict = q.to_dict()
                q_dict["order_num"] = eq.order_num
                q_dict["exam_score"] = eq.score
                questions.append(q_dict)
        exam_dict["questions"] = questions

        return exam_dict

    @staticmethod
    def create(db: Session, data: dict, user_id: int) -> Tuple[Optional[Exam], str]:
        """创建考试"""
        exam = Exam(
            name=data["name"],
            description=data.get("description"),
            start_time=data.get("start_time"),
            duration=data.get("duration", 60),
            total_score=data.get("total_score", 100),
            pass_score=data.get("pass_score", 60),
            mode=data.get("mode", "fixed"),
            status="draft",
            shuffle_question=int(data.get("shuffle_question", False)),
            shuffle_option=int(data.get("shuffle_option", False)),
            allow_early_submit=int(data.get("allow_early_submit", True)),
            random_config=data.get("random_config"),
            notice=data.get("notice"),
            created_by=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(exam)
        db.flush()

        # 关联班级
        for class_id in data.get("class_ids", []):
            exam_class = ExamClass(exam_id=exam.id, class_id=class_id)
            db.add(exam_class)

        # 关联题目（固定模式）
        if exam.mode == "fixed":
            for q_data in data.get("questions", []):
                eq = ExamQuestion(
                    exam_id=exam.id,
                    question_id=q_data["question_id"],
                    order_num=q_data.get("order_num", 0),
                    score=q_data.get("score", 2),
                )
                db.add(eq)
        elif exam.mode == "random" and data.get("random_config"):
            # 随机组卷 - 在发布时生成题目
            pass

        db.commit()
        db.refresh(exam)
        return exam, "创建成功"

    @staticmethod
    def update(db: Session, exam_id: int, data: dict) -> Tuple[Optional[Exam], str]:
        """更新考试"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None, "考试不存在"

        # 只有草稿状态可编辑
        if exam.status not in ("draft", "published"):
            return None, "当前状态不允许编辑"

        for field in ["name", "description", "start_time", "duration", "total_score",
                       "pass_score", "mode", "shuffle_question", "shuffle_option",
                       "allow_early_submit", "random_config", "notice"]:
            if field in data and data[field] is not None:
                if field in ("shuffle_question", "shuffle_option", "allow_early_submit"):
                    setattr(exam, field, int(data[field]))
                else:
                    setattr(exam, field, data[field])

        # 更新班级关联
        if "class_ids" in data and data["class_ids"] is not None:
            db.query(ExamClass).filter(ExamClass.exam_id == exam_id).delete()
            for class_id in data["class_ids"]:
                db.add(ExamClass(exam_id=exam_id, class_id=class_id))

        # 更新题目关联（固定模式）
        if "questions" in data and data["questions"] is not None and exam.mode == "fixed":
            db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).delete()
            for q_data in data["questions"]:
                db.add(ExamQuestion(
                    exam_id=exam_id,
                    question_id=q_data["question_id"],
                    order_num=q_data.get("order_num", 0),
                    score=q_data.get("score", 2),
                ))

        exam.updated_at = datetime.now()
        db.commit()
        db.refresh(exam)
        return exam, "更新成功"

    @staticmethod
    def delete(db: Session, exam_id: int) -> Tuple[bool, str]:
        """删除考试（允许删除所有状态的考试）"""
        import logging
        logger = logging.getLogger(__name__)

        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return False, "考试不存在"

        # 检查是否有进行中的会话（记录日志，但仍允许删除）
        from models.session import ExamSession
        active_sessions = db.query(ExamSession).filter(
            ExamSession.exam_id == exam_id,
            ExamSession.status == "in_progress",
        ).count()
        if active_sessions > 0:
            logger.warning(f"删除考试 {exam_id}({exam.name})，该考试有 {active_sessions} 个进行中的会话")

        logger.info(f"删除考试: id={exam_id}, name={exam.name}, status={exam.status}")

        db.delete(exam)
        db.commit()
        return True, "删除成功"

    @staticmethod
    def publish(db: Session, exam_id: int) -> Tuple[Optional[Exam], str]:
        """发布考试"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None, "考试不存在"
        if exam.status != "draft":
            return None, "只有草稿状态可以发布"

        # 随机组卷生成题目
        if exam.mode == "random" and exam.random_config:
            ExamService._generate_random_questions(db, exam)

        # 检查是否有题目
        q_count = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).count()
        if q_count == 0:
            return None, "考试没有题目，无法发布"

        # 检查是否有参考班级
        c_count = db.query(ExamClass).filter(ExamClass.exam_id == exam_id).count()
        if c_count == 0:
            return None, "考试没有参考班级，无法发布"

        exam.status = "published"
        exam.updated_at = datetime.now()
        db.commit()
        db.refresh(exam)
        return exam, "发布成功"

    @staticmethod
    def pause(db: Session, exam_id: int) -> Tuple[Optional[Exam], str]:
        """暂停考试"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None, "考试不存在"
        if exam.status != "ongoing":
            return None, "只有进行中的考试可以暂停"

        exam.status = "paused"
        exam.updated_at = datetime.now()
        db.commit()
        db.refresh(exam)
        return exam, "考试已暂停"

    @staticmethod
    def resume(db: Session, exam_id: int) -> Tuple[Optional[Exam], str]:
        """恢复考试"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None, "考试不存在"
        if exam.status != "paused":
            return None, "只有暂停的考试可以恢复"

        exam.status = "ongoing"
        exam.updated_at = datetime.now()
        db.commit()
        db.refresh(exam)
        return exam, "考试已恢复"

    @staticmethod
    def terminate(db: Session, exam_id: int) -> Tuple[Optional[Exam], str]:
        """终止考试"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None, "考试不存在"
        if exam.status not in ("ongoing", "paused", "published"):
            return None, "当前状态不允许终止"

        # 自动提交所有未提交的会话
        from models.session import ExamSession
        from services.session_service import SessionService
        active_sessions = db.query(ExamSession).filter(
            ExamSession.exam_id == exam_id,
            ExamSession.status == "in_progress",
        ).all()
        for session in active_sessions:
            SessionService.force_submit(db, session.id, "考试被终止，自动提交")

        exam.status = "ended"
        exam.updated_at = datetime.now()
        db.commit()
        db.refresh(exam)
        return exam, "考试已终止"

    @staticmethod
    def archive(db: Session, exam_id: int) -> Tuple[Optional[Exam], str]:
        """归档考试"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None, "考试不存在"
        if exam.status != "ended":
            return None, "只有已结束的考试可以归档"

        exam.status = "archived"
        exam.updated_at = datetime.now()
        db.commit()
        db.refresh(exam)
        return exam, "考试已归档"

    @staticmethod
    def reactivate(db: Session, exam_id: int) -> Tuple[Optional[Exam], str]:
        """重新激活已结束的考试，同时重置所有旧会话并更新开始时间"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None, "考试不存在"
        if exam.status not in ("ended", "archived"):
            return None, "只有已结束或已归档的考试可以重新激活"

        # 1. 更新考试状态和开始时间
        exam.status = "published"
        exam.start_time = datetime.now()
        exam.updated_at = datetime.now()

        # 2. 删除旧的答题记录，并重置该考试下所有考生会话
        db.query(Answer).filter(
            Answer.session_id.in_(
                db.query(ExamSession.id).filter(ExamSession.exam_id == exam_id)
            )
        ).delete(synchronize_session=False)

        reset_count = db.query(ExamSession).filter(
            ExamSession.exam_id == exam_id
        ).update({
            "status": "not_started",
            "start_time": None,
            "submit_time": None,
            "time_used": None,
            "total_score": None,
            "extra_time": 0,
            "is_active": True,
        }, synchronize_session=False)

        db.commit()
        db.refresh(exam)
        return exam, f"考试已重新激活，状态变为已发布，已重置 {reset_count} 名考生会话"

    @staticmethod
    def check_and_update_status(db: Session) -> None:
        """检查并更新考试状态（定时任务调用）"""
        now = datetime.now()

        # published → ongoing（到达开始时间）
        exams = db.query(Exam).filter(Exam.status == "published").all()
        for exam in exams:
            if exam.start_time and now >= exam.start_time:
                exam.status = "ongoing"
                exam.updated_at = now
                # 创建会话记录
                ExamService._create_sessions_for_exam(db, exam)

        # ongoing → ended（到达结束时间）
        exams = db.query(Exam).filter(Exam.status == "ongoing").all()
        for exam in exams:
            if exam.start_time:
                end_time = exam.start_time + __import__("datetime").timedelta(minutes=exam.duration)
                if now >= end_time:
                    # 自动提交
                    from models.session import ExamSession
                    from services.session_service import SessionService
                    active = db.query(ExamSession).filter(
                        ExamSession.exam_id == exam.id,
                        ExamSession.status == "in_progress",
                    ).all()
                    for session in active:
                        SessionService.auto_submit(db, session.id)
                    exam.status = "ended"
                    exam.updated_at = now

        db.commit()

    @staticmethod
    def _create_sessions_for_exam(db: Session, exam: Exam) -> None:
        """为考试的所有参考学生创建会话"""
        exam_classes = db.query(ExamClass).filter(ExamClass.exam_id == exam.id).all()
        class_ids = [ec.class_id for ec in exam_classes]

        if not class_ids:
            return

        students = db.query(User).filter(
            User.class_id.in_(class_ids),
            User.role == "student",
            User.status == "active",
        ).all()

        from models.session import ExamSession
        for student in students:
            # 检查是否已存在
            existing = db.query(ExamSession).filter(
                ExamSession.exam_id == exam.id,
                ExamSession.user_id == student.id,
            ).first()
            if not existing:
                session = ExamSession(
                    exam_id=exam.id,
                    user_id=student.id,
                    status="not_started",
                    is_active=1,
                    created_at=datetime.now(),
                )
                db.add(session)
        db.flush()

    @staticmethod
    def _generate_random_questions(db: Session, exam: Exam) -> None:
        """随机组卷 - 根据配置从题库随机抽取题目"""
        import random
        config = exam.random_config or {}

        total_score = 0

        # 优先使用按题型抽取规则
        type_rules = config.get("type_rules")
        if type_rules:
            for rule in type_rules:
                q_type = rule.get("type")
                count = rule.get("count", 0)
                score_per = rule.get("score_per_question", 2)
                cat_id = rule.get("category_id")
                difficulty = rule.get("difficulty")

                if not q_type or count <= 0:
                    continue

                query = db.query(Question).filter(Question.type == q_type)
                if cat_id:
                    query = query.filter(Question.category_id == cat_id)
                if difficulty:
                    query = query.filter(Question.difficulty == difficulty)

                pool = query.all()
                actual_count = min(count, len(pool))
                if actual_count == 0:
                    continue

                selected = random.sample(pool, actual_count)
                # 先删除该题型旧数据
                for idx, q in enumerate(selected):
                    eq = ExamQuestion(
                        exam_id=exam.id,
                        question_id=q.id,
                        order_num=idx + 1,
                        score=score_per,
                    )
                    db.add(eq)
                    total_score += score_per
        else:
            # 通用随机抽取（向后兼容）
            category_id = config.get("category_id")
            difficulty = config.get("difficulty")
            count = config.get("count", 10)
            score_per = config.get("score_per_question", 2)

            query = db.query(Question)
            if category_id:
                query = query.filter(Question.category_id == category_id)
            if difficulty:
                query = query.filter(Question.difficulty == difficulty)

            questions = query.all()
            actual_count = min(count, len(questions))

            selected = random.sample(questions, actual_count)
            for idx, q in enumerate(selected):
                eq = ExamQuestion(
                    exam_id=exam.id,
                    question_id=q.id,
                    order_num=idx + 1,
                    score=score_per,
                )
                db.add(eq)
                total_score += score_per

        # 更新总分和及格线
        if total_score > 0:
            exam.total_score = total_score
            exam.pass_score = int(total_score * 0.6)
        db.flush()

    @staticmethod
    def set_exam_questions(db: Session, exam_id: int, questions: List[dict]) -> Tuple[bool, str]:
        """设置考试题目（仅草稿状态可设置）"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return False, "考试不存在"
        if exam.status != "draft":
            return False, "仅草稿状态的考试可以设置题目"

        # 删除旧的题目关联
        db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).delete()

        # 创建新的题目关联
        total_score = 0
        for idx, item in enumerate(questions):
            question_id = item.get("question_id")
            score = item.get("score", 0)
            q = db.query(Question).filter(Question.id == question_id).first()
            if not q:
                db.rollback()
                return False, f"题目 {question_id} 不存在"
            eq = ExamQuestion(
                exam_id=exam_id,
                question_id=question_id,
                order_num=idx + 1,
                score=score,
            )
            db.add(eq)
            total_score += score

        # 更新总分和及格线
        exam.total_score = total_score
        exam.pass_score = int(total_score * 0.6)
        db.flush()
        return True, "设置成功"

    @staticmethod
    def get_exam_questions_for_admin(db: Session, exam_id: int) -> list:
        """获取考试题目列表（管理员视角，含正确答案）"""
        exam_questions = (
            db.query(ExamQuestion)
            .filter(ExamQuestion.exam_id == exam_id)
            .order_by(ExamQuestion.order_num)
            .all()
        )
        result = []
        for eq in exam_questions:
            q = db.query(Question).filter(Question.id == eq.question_id).first()
            if q:
                q_dict = q.to_dict()
                q_dict["order_num"] = eq.order_num
                q_dict["exam_score"] = eq.score
                result.append(q_dict)
        return result

    @staticmethod
    def get_exam_classes(db: Session, exam_id: int) -> list:
        """获取考试关联班级"""
        exam_classes = db.query(ExamClass).filter(ExamClass.exam_id == exam_id).all()
        result = []
        for ec in exam_classes:
            cls = db.query(Class).filter(Class.id == ec.class_id).first()
            if cls:
                result.append({"id": cls.id, "name": cls.name})
        return result
