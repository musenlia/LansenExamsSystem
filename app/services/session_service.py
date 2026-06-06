# -*- coding: utf-8 -*-
"""考试会话服务 - 进入考试、获取题目、保存答案、提交答卷、自动评分"""

import json
from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from models.session import ExamSession
from models.exam import Exam, ExamQuestion, ExamClass
from models.answer import Answer
from models.question import Question
from models.user import User
from models.class_ import Class
from models.monitor_log import MonitorLog
from utils.shuffle import generate_question_order, generate_option_order
from utils.grading import grade_question


class SessionService:
    """考试会话服务"""

    @staticmethod
    def get_my_exams(db: Session, user_id: int) -> list:
        """获取考生的考试列表"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.class_id:
            return []

        # 获取该班级参加的考试
        exam_classes = db.query(ExamClass).filter(ExamClass.class_id == user.class_id).all()
        exam_ids = [ec.exam_id for ec in exam_classes]

        exams = db.query(Exam).filter(Exam.id.in_(exam_ids)).all()
        result = []
        for exam in exams:
            exam_dict = exam.to_dict()
            # 查找该考生的会话
            session = db.query(ExamSession).filter(
                ExamSession.exam_id == exam.id,
                ExamSession.user_id == user_id,
            ).first()
            exam_dict["session_id"] = session.id if session else None
            exam_dict["session_status"] = session.status if session else None
            exam_dict["total_score_earned"] = session.total_score if session else None
            result.append(exam_dict)

        return result

    @staticmethod
    def _check_exam_time(db: Session, exam: Exam) -> None:
        """检查考试时间，自动更新状态 published->ongoing / ongoing->ended"""
        now = datetime.now()
        end_time = None
        if exam.start_time and exam.duration:
            end_time = datetime.fromtimestamp(exam.start_time.timestamp() + exam.duration * 60)

        if exam.status == "published" and exam.start_time and now >= exam.start_time:
            exam.status = "ongoing"
            db.commit()
        elif exam.status == "ongoing" and end_time and now >= end_time:
            exam.status = "ended"
            db.commit()

    @staticmethod
    def enter_exam(db: Session, user_id: int, exam_id: int) -> Tuple[Optional[ExamSession], str]:
        """
        进入考试 - 创建或获取会话，生成乱序

        每位考生对每场考试有且仅有一个会话
        """
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None, "考试不存在"

        # 自动更新考试时间状态
        SessionService._check_exam_time(db, exam)
        db.refresh(exam)

        # 检查考试状态
        if exam.status not in ("published", "ongoing"):
            return None, "考试当前不可进入"

        # 检查考试时间
        if exam.start_time and datetime.now() < exam.start_time:
            return None, "考试尚未开始"

        # 查找或创建会话
        session = db.query(ExamSession).filter(
            ExamSession.exam_id == exam_id,
            ExamSession.user_id == user_id,
        ).first()

        if session:
            # 已有会话
            if session.status == "submitted" or session.status == "force_submitted" or session.status == "auto_submitted":
                return None, "您已提交答卷，不能再次进入"
            if session.status == "in_progress":
                # 检查是否超时
                if session.start_time and exam.duration:
                    elapsed = (datetime.now() - session.start_time).total_seconds()
                    effective_duration = exam.duration * 60 + (session.extra_time or 0)
                    if elapsed > effective_duration:
                        SessionService.auto_submit(db, session.id)
                        return None, "考试时间已到，答卷已自动提交"
                return session, "继续答题"
        else:
            # 检查是否有权限参加
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.class_id:
                return None, "您没有参加此考试的权限"

            exam_class = db.query(ExamClass).filter(
                ExamClass.exam_id == exam_id,
                ExamClass.class_id == user.class_id,
            ).first()
            if not exam_class:
                return None, "您没有参加此考试的权限"

            # 创建新会话
            session = ExamSession(
                exam_id=exam_id,
                user_id=user_id,
                status="not_started",
                is_active=1,
                created_at=datetime.now(),
            )
            db.add(session)
            db.flush()

        # 开始答题
        if session.status == "not_started":
            session.status = "in_progress"
            session.start_time = datetime.now()

            # 生成题目乱序
            exam_questions = (
                db.query(ExamQuestion)
                .filter(ExamQuestion.exam_id == exam_id)
                .order_by(ExamQuestion.order_num)
                .all()
            )
            question_ids = [eq.question_id for eq in exam_questions]

            if exam.shuffle_question:
                question_order = generate_question_order(question_ids, shuffle=True)
            else:
                question_order = question_ids
            session.question_order = question_order

            # 为每道题生成选项乱序并创建 answer 记录
            for idx, q_id in enumerate(question_order):
                eq = next((e for e in exam_questions if e.question_id == q_id), None)
                q = db.query(Question).filter(Question.id == q_id).first()
                if not q or not eq:
                    continue

                option_order = None
                if q.type in ("single", "multiple") and q.options and exam.shuffle_option:
                    # 兼容 list 和 dict 两种 options 格式
                    if isinstance(q.options, list):
                        option_count = len(q.options)
                    elif isinstance(q.options, dict):
                        option_count = len(q.options)
                    else:
                        option_count = 0
                    if option_count > 0:
                        option_order = generate_option_order(option_count, shuffle=True)

                answer = Answer(
                    session_id=session.id,
                    question_id=q_id,
                    option_order=option_order,
                    answered_at=None,
                )
                db.add(answer)

            db.commit()
            db.refresh(session)

        return session, "进入考试成功"

    @staticmethod
    def get_questions(db: Session, session_id: int, user_id: int) -> Optional[dict]:
        """获取考试题目列表（考生视角，不含正确答案）"""
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return None
        if session.user_id != user_id:
            return None

        # 自动更新考试时间状态
        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        if exam:
            SessionService._check_exam_time(db, exam)
            db.refresh(exam)

        # 如果状态是 not_started，自动重新进入考试
        if session.status == "not_started":
            # 检查考试是否允许进入
            if not exam or exam.status not in ("published", "ongoing"):
                return None
            if exam.start_time and datetime.now() < exam.start_time:
                return None

            # 重新进入考试
            session.status = "in_progress"
            session.start_time = datetime.now()
            session.submit_time = None
            session.time_used = None
            session.total_score = None
            session.extra_time = 0

            # 生成题目乱序
            exam_questions = (
                db.query(ExamQuestion)
                .filter(ExamQuestion.exam_id == exam.id)
                .order_by(ExamQuestion.order_num)
                .all()
            )
            question_ids = [eq.question_id for eq in exam_questions]

            if exam.shuffle_question:
                question_order = generate_question_order(question_ids, shuffle=True)
            else:
                question_order = question_ids
            session.question_order = question_order

            # 为每道题生成选项乱序并创建 answer 记录
            for idx, q_id in enumerate(question_order):
                eq = next((e for e in exam_questions if e.question_id == q_id), None)
                q = db.query(Question).filter(Question.id == q_id).first()
                if not q or not eq:
                    continue

                option_order = None
                if q.type in ("single", "multiple") and q.options and exam.shuffle_option:
                    if isinstance(q.options, list):
                        option_count = len(q.options)
                    elif isinstance(q.options, dict):
                        option_count = len(q.options)
                    else:
                        option_count = 0
                    if option_count > 0:
                        option_order = generate_option_order(option_count, shuffle=True)

                answer = Answer(
                    session_id=session.id,
                    question_id=q_id,
                    option_order=option_order,
                    answered_at=None,
                )
                db.add(answer)

            db.commit()
            db.refresh(session)

        if session.status != "in_progress":
            return None

        # exam 变量在 _check_exam_time 后仍有效
        if not exam:
            return None

        # 检查是否超时
        if session.start_time and exam.duration:
            elapsed = (datetime.now() - session.start_time).total_seconds()
            effective_duration = exam.duration * 60 + (session.extra_time or 0)
            if elapsed > effective_duration:
                SessionService.auto_submit(db, session.id)
                return {"_timeout": True, "session_id": session.id}

        # 获取乱序题目列表
        question_order = session.question_order or []
        answers = db.query(Answer).filter(Answer.session_id == session_id).all()
        answer_map = {a.question_id: a for a in answers}

        questions = []
        for idx, q_id in enumerate(question_order):
            q = db.query(Question).filter(Question.id == q_id).first()
            answer = answer_map.get(q_id)
            eq = db.query(ExamQuestion).filter(
                ExamQuestion.exam_id == exam.id,
                ExamQuestion.question_id == q_id,
            ).first()

            if not q:
                continue

            # 构建选项（按乱序排列）
            # options 可能是 list（[{"label":"A","content":"xxx"}]）或 dict（{"A":"xxx"}）
            options_list = None
            if q.options:
                if isinstance(q.options, list):
                    # list 格式：[{"label":"A","content":"xxx"}, ...]
                    raw_items = q.options  # list of dicts
                    if answer and answer.option_order:
                        options_list = [
                            raw_items[i]
                            for i in answer.option_order
                            if i < len(raw_items)
                        ]
                    else:
                        options_list = raw_items
                elif isinstance(q.options, dict):
                    # dict 格式：{"A":"xxx", "B":"yyy"}（旧格式兼容）
                    if answer and answer.option_order:
                        items = list(q.options.items())
                        options_list = [
                            {"key": items[i][0], "value": items[i][1]}
                            for i in answer.option_order
                            if i < len(items)
                        ]
                    else:
                        options_list = [
                            {"key": k, "value": v}
                            for k, v in q.options.items()
                        ]

            q_data = {
                "order_num": idx + 1,
                "question_id": q.id,
                "type": q.type,
                "content": q.content,
                "options": options_list,
                "score": eq.score if eq else q.score,
                "difficulty": q.difficulty,
                "fill_match_mode": q.fill_match_mode,
                "user_answer": answer.user_answer if answer else None,
                "is_flagged": bool(answer.is_flagged) if answer and answer.is_flagged else False,
            }
            questions.append(q_data)

        # 计算剩余时间
        remaining = None
        if session.start_time and exam.duration:
            elapsed = (datetime.now() - session.start_time).total_seconds()
            effective_duration = exam.duration * 60 + (session.extra_time or 0)
            remaining = max(0, int(effective_duration - elapsed))

        return {
            "session_id": session.id,
            "exam_name": exam.name,
            "duration": exam.duration,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "remaining_seconds": remaining,
            "extra_time": session.extra_time or 0,
            "total_questions": len(questions),
            "questions": questions,
        }

    @staticmethod
    def save_answer(
        db: Session,
        session_id: int,
        question_id: int,
        user_id: int,
        user_answer: str,
    ) -> Tuple[bool, str, Optional[dict]]:
        """保存答案，返回 (success, message, auto_submit_result)"""
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return False, "会话不存在", None
        if session.user_id != user_id:
            return False, "无权操作", None
        if session.status != "in_progress":
            return False, "不在答题状态", None

        # 检查是否超时
        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        if session.start_time and exam and exam.duration:
            elapsed = (datetime.now() - session.start_time).total_seconds()
            effective_duration = exam.duration * 60 + (session.extra_time or 0)
            if elapsed > effective_duration:
                SessionService.auto_submit(db, session.id)
                return False, "考试已超时，已自动交卷", {
                    "auto_submitted": True,
                    "session_id": session.id,
                }

        answer = db.query(Answer).filter(
            Answer.session_id == session_id,
            Answer.question_id == question_id,
        ).first()

        if answer:
            answer.user_answer = user_answer
            answer.answered_at = datetime.now()
        else:
            answer = Answer(
                session_id=session_id,
                question_id=question_id,
                user_answer=user_answer,
                answered_at=datetime.now(),
            )
            db.add(answer)

        db.commit()
        # 计算当前剩余时间
        remaining = None
        if session.start_time and exam and exam.duration:
            elapsed = (datetime.now() - session.start_time).total_seconds()
            effective_duration = exam.duration * 60 + (session.extra_time or 0)
            remaining = max(0, int(effective_duration - elapsed))

        # 推送监控更新（异步，不阻塞保存）
        try:
            import asyncio
            from services.monitor_service import MonitorService, ws_manager
            student_data = MonitorService.get_students(db, session.exam_id)
            matching = [s for s in student_data if s["session_id"] == session_id]
            if matching:
                loop = asyncio.get_event_loop()
                loop.create_task(ws_manager.broadcast_to_exam(session.exam_id, {
                    "type": "student_update",
                    "exam_id": session.exam_id,
                    "session_id": session_id,
                    "student": matching[0],
                }))
        except Exception:
            pass  # 推送失败不影响保存

        return True, "保存成功", {"remaining_seconds": remaining, "extra_time": session.extra_time or 0}

    @staticmethod
    def toggle_flag(db: Session, session_id: int, question_id: int, user_id: int, is_flagged: bool) -> Tuple[bool, str, bool]:
        """标记/取消标记题目，返回 (success, message, new_flag_state)"""
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return False, "会话不存在", False
        if session.user_id != user_id:
            return False, "无权操作", False
        if session.status != "in_progress":
            return False, "不在答题状态", False

        answer = db.query(Answer).filter(
            Answer.session_id == session_id,
            Answer.question_id == question_id,
        ).first()
        if not answer:
            return False, "答题记录不存在", False

        answer.is_flagged = 1 if is_flagged else 0
        db.commit()
        return True, "success", is_flagged

    @staticmethod
    def submit_exam(db: Session, session_id: int, user_id: int) -> Tuple[bool, str, Optional[dict]]:
        """提交答卷，返回成绩数据"""
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return False, "会话不存在", None
        if session.user_id != user_id:
            return False, "无权操作", None
        if session.status != "in_progress":
            return False, "不在答题状态", None

        # 检查是否允许提前交卷
        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        if exam and not exam.allow_early_submit:
            # 检查是否到了结束时间
            if session.start_time and exam.duration:
                elapsed = (datetime.now() - session.start_time).total_seconds()
                if elapsed < exam.duration * 60:
                    return False, "不允许提前交卷", None

        session.status = "submitted"
        session.submit_time = datetime.now()
        if session.start_time:
            session.time_used = int((datetime.now() - session.start_time).total_seconds())
        session.is_active = 0

        # 自动评分
        SessionService._auto_grade(db, session)

        db.commit()
        db.refresh(session)

        # 推送监控更新
        try:
            import asyncio
            from services.monitor_service import MonitorService, ws_manager
            overview = MonitorService.get_overview(db, session.exam_id)
            students = MonitorService.get_students(db, session.exam_id)
            matching = [s for s in students if s["session_id"] == session_id]
            loop = asyncio.get_event_loop()
            if matching:
                loop.create_task(ws_manager.broadcast_to_exam(session.exam_id, {
                    "type": "student_update",
                    "exam_id": session.exam_id,
                    "session_id": session_id,
                    "student": matching[0],
                }))
            if overview:
                loop.create_task(ws_manager.broadcast_to_exam(session.exam_id, {
                    "type": "overview_update",
                    "exam_id": session.exam_id,
                    "overview": overview,
                }))
        except Exception:
            pass

        # 构建成绩数据
        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        result_data = {
            "session_id": session.id,
            "total_score": session.total_score,
            "pass_score": exam.pass_score if exam else 0,
            "is_passed": (session.total_score or 0) >= (exam.pass_score if exam else 0) if session.total_score is not None else None,
            "time_used": session.time_used,
            "status": session.status,
        }

        return True, "提交成功", result_data

    @staticmethod
    def auto_submit(db: Session, session_id: int) -> None:
        """自动提交（到时间）"""
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session or session.status != "in_progress":
            return

        session.status = "auto_submitted"
        session.submit_time = datetime.now()
        if session.start_time:
            session.time_used = int((datetime.now() - session.start_time).total_seconds())
        session.is_active = 0

        SessionService._auto_grade(db, session)
        db.commit()

    @staticmethod
    def force_submit(db: Session, session_id: int, reason: str = "管理员强制交卷") -> Tuple[bool, str]:
        """强制交卷"""
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return False, "会话不存在"
        if session.status != "in_progress":
            return False, "不在答题状态"

        session.status = "force_submitted"
        session.submit_time = datetime.now()
        if session.start_time:
            session.time_used = int((datetime.now() - session.start_time).total_seconds())
        session.is_active = 0

        SessionService._auto_grade(db, session)

        # 记录监控日志
        log = MonitorLog(
            session_id=session_id,
            user_id=session.user_id,
            exam_id=session.exam_id,
            event_type="force_submit",
            event_time=datetime.now(),
            detail=reason,
        )
        db.add(log)
        db.commit()
        return True, "强制交卷成功"

    @staticmethod
    def get_result(db: Session, session_id: int, user_id: int, role: str = "student") -> Optional[dict]:
        """
        获取考试结果

        Args:
            db: 数据库会话
            session_id: 会话ID
            user_id: 用户ID（student查看自己的，admin/teacher可查看任意）
            role: 当前用户角色，student仅返回分数概览，admin/teacher返回完整详情

        Returns:
            考试结果字典
        """
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return None

        # 学生只能查看自己的结果
        if role == "student" and session.user_id != user_id:
            return None

        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        if not exam:
            return None

        # 基础概览数据（所有角色可见）
        result = {
            "session_id": session.id,
            "exam_name": exam.name,
            "total_score": session.total_score,
            "pass_score": exam.pass_score,
            "is_passed": (session.total_score or 0) >= exam.pass_score if session.total_score is not None else None,
            "status": session.status,
            "time_used": session.time_used,
            "submit_time": session.submit_time.isoformat() if session.submit_time else None,
        }

        # admin/teacher 可以查看完整详情（含答题明细）
        if role in ("admin", "teacher"):
            answers = db.query(Answer).filter(Answer.session_id == session_id).all()
            answer_details = []
            for answer in answers:
                question = db.query(Question).filter(Question.id == answer.question_id).first()
                if question:
                    answer_details.append({
                        "id": answer.id,
                        "question_id": question.id,
                        "type": question.type,
                        "content": question.content,
                        "options": question.options,
                        "user_answer": answer.user_answer,
                        "correct_answer": question.answer,
                        "score": answer.score,
                        "max_score": question.score,
                        "is_correct": bool(answer.is_correct) if answer.is_correct is not None else None,
                        "analysis": question.analysis,
                    })
            result["details"] = answer_details

        return result

    @staticmethod
    def _auto_grade(db: Session, session: ExamSession) -> None:
        """自动评分"""
        answers = db.query(Answer).filter(Answer.session_id == session.id).all()
        total = 0

        for answer in answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            if not question or not answer.user_answer:
                answer.score = 0
                answer.is_correct = 0
                continue

            # 获取该题在考试中的分值
            eq = db.query(ExamQuestion).filter(
                ExamQuestion.exam_id == session.exam_id,
                ExamQuestion.question_id == answer.question_id,
            ).first()
            score = eq.score if eq else question.score

            is_correct, earned = grade_question(
                question_type=question.type,
                user_answer=answer.user_answer,
                correct_answer=question.answer,
                fill_match_mode=question.fill_match_mode,
                score=score,
            )
            answer.score = earned
            answer.is_correct = 1 if is_correct else 0
            total += earned

        session.total_score = total

    @staticmethod
    def reset_exam(db: Session, session_id: int) -> Tuple[bool, str]:
        """
        重置考试 - 将已交卷的会话重置为未开始状态，清空答题记录和分数

        Args:
            db: 数据库会话
            session_id: 会话ID

        Returns:
            (success, message)
        """
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return False, "会话不存在"

        if session.status not in ("submitted", "force_submitted", "auto_submitted"):
            return False, "只能重置已交卷的会话"

        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        if not exam:
            return False, "考试不存在"

        db.query(Answer).filter(Answer.session_id == session_id).delete()

        session.status = "not_started"
        session.start_time = None
        session.submit_time = None
        session.time_used = None
        session.total_score = None
        session.question_order = None
        session.is_active = 1
        session.extra_time = 0

        log = MonitorLog(
            session_id=session_id,
            user_id=session.user_id,
            exam_id=session.exam_id,
            event_type="reset",
            event_time=datetime.now(),
            detail="管理员重置考试",
        )
        db.add(log)
        db.commit()
        return True, "重置成功，考生可以重新作答"

    @staticmethod
    def resume_exam(db: Session, session_id: int) -> Tuple[bool, str]:
        """
        续考 - 将已交卷/超时的考生会话恢复为答题中状态，保留答题记录

        Args:
            db: 数据库会话
            session_id: 会话ID

        Returns:
            (success, message)
        """
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return False, "会话不存在"

        if session.status not in ("submitted", "force_submitted", "auto_submitted"):
            return False, "只能恢复已交卷的会话"

        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        if not exam:
            return False, "考试不存在"

        if exam.status not in ("published", "ongoing"):
            return False, "考试当前状态不允许续考"

        session.status = "in_progress"
        session.start_time = datetime.now()
        session.submit_time = None
        session.time_used = None
        session.total_score = None
        session.is_active = 1
        session.extra_time = session.extra_time or 0

        log = MonitorLog(
            session_id=session_id,
            user_id=session.user_id,
            exam_id=session.exam_id,
            event_type="resume",
            event_time=datetime.now(),
            detail="管理员恢复续考",
        )
        db.add(log)
        db.commit()
        return True, "续考成功，考生可以继续答题"

    @staticmethod
    def add_extra_time(db: Session, session_id: int, extra_minutes: int) -> Tuple[bool, str]:
        """
        补时 - 为正在答题的考生增加额外考试时间

        Args:
            db: 数据库会话
            session_id: 会话ID
            extra_minutes: 额外时间(分钟)

        Returns:
            (success, message)
        """
        if extra_minutes <= 0:
            return False, "额外时间必须大于0"

        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return False, "会话不存在"

        if session.status != "in_progress":
            return False, "只能为正在答题的会话补时"

        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        if not exam:
            return False, "考试不存在"

        current_extra = session.extra_time or 0
        session.extra_time = current_extra + extra_minutes * 60

        log = MonitorLog(
            session_id=session_id,
            user_id=session.user_id,
            exam_id=session.exam_id,
            event_type="extra_time",
            event_time=datetime.now(),
            detail=f"管理员补时: +{extra_minutes}分钟",
        )
        db.add(log)
        db.commit()
        return True, f"补时成功，已增加 {extra_minutes} 分钟"
