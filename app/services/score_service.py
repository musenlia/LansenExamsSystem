# -*- coding: utf-8 -*-
"""成绩服务 - 成绩列表、答卷详情、统计、Excel导出"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.session import ExamSession
from models.exam import Exam
from models.answer import Answer
from models.question import Question
from models.user import User
from models.class_ import Class
from utils.excel_helper import create_score_export


class ScoreService:
    """成绩服务"""

    @staticmethod
    def get_score_list(
        db: Session,
        exam_id: int,
        page: int = 1,
        size: int = 20,
        keyword: Optional[str] = None,
        class_id: Optional[int] = None,
    ) -> dict:
        """获取成绩列表"""
        query = db.query(ExamSession).filter(ExamSession.exam_id == exam_id)

        # 关联用户过滤
        if keyword or class_id:
            query = query.join(User, ExamSession.user_id == User.id)
            if keyword:
                query = query.filter(
                    (User.username.contains(keyword)) | (User.name.contains(keyword))
                )
            if class_id:
                query = query.filter(User.class_id == class_id)

        total = query.count()
        sessions = query.order_by(ExamSession.id.desc()).offset((page - 1) * size).limit(size).all()

        # 查询考试的 pass_score
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        pass_score = exam.pass_score if exam else 0

        items = []
        for session in sessions:
            user = db.query(User).filter(User.id == session.user_id).first()
            class_name = None
            if user and user.class_id:
                cls = db.query(Class).filter(Class.id == user.class_id).first()
                class_name = cls.name if cls else None

            score = session.total_score
            items.append({
                "session_id": session.id,
                "user_id": session.user_id,
                "username": user.username if user else "",
                "name": user.name if user else "",
                "class_name": class_name,
                "total_score": session.total_score,
                "score": score,
                "is_passed": bool(score >= pass_score) if (score is not None and pass_score) else None,
                "duration_seconds": session.time_used or 0,
                "status": session.status,
                "time_used": session.time_used,
                "submit_time": session.submit_time.isoformat() if session.submit_time else None,
                "start_time": session.start_time.isoformat() if session.start_time else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def get_score_detail(db: Session, session_id: int) -> Optional[dict]:
        """获取答卷详情"""
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if not session:
            return None

        exam = db.query(Exam).filter(Exam.id == session.exam_id).first()
        user = db.query(User).filter(User.id == session.user_id).first()

        # 获取答题记录
        answers = db.query(Answer).filter(Answer.session_id == session_id).all()
        question_details = []
        for answer in answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            if question:
                # options 兼容 list 和 dict 格式
                options = question.options
                if options and isinstance(options, dict):
                    options = [
                        {"label": k, "content": v}
                        for k, v in options.items()
                    ]

                question_details.append({
                    "id": answer.id,
                    "question_id": question.id,
                    "type": question.type,
                    "content": question.content,
                    "options": options,
                    "student_answer": answer.user_answer,
                    "correct_answer": question.answer,
                    "score": answer.score,
                    "max_score": question.score,
                    "is_correct": bool(answer.is_correct) if answer.is_correct is not None else None,
                    "analysis": question.analysis,
                })

        class_name = None
        if user and user.class_id:
            cls = db.query(Class).filter(Class.id == user.class_id).first()
            class_name = cls.name if cls else None

        return {
            "session_id": session.id,
            "exam_id": session.exam_id,
            "exam_name": exam.name if exam else "",
            "user_id": session.user_id,
            "username": user.username if user else "",
            "name": user.name if user else "",
            "class_name": class_name,
            "total_score": session.total_score,
            "score": session.total_score,
            "pass_score": exam.pass_score if exam else 0,
            "is_passed": bool(session.total_score >= exam.pass_score) if (exam and session.total_score is not None) else None,
            "duration_seconds": session.time_used or 0,
            "status": session.status,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "submit_time": session.submit_time.isoformat() if session.submit_time else None,
            "time_used": session.time_used,
            "questions": question_details,
        }

    @staticmethod
    def get_stats(db: Session, exam_id: int) -> Optional[dict]:
        """获取成绩统计"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        sessions = db.query(ExamSession).filter(
            ExamSession.exam_id == exam_id,
            ExamSession.total_score.isnot(None),
        ).all()

        if not sessions:
            return {
                "exam_id": exam.id,
                "exam_name": exam.name,
                "total_students": 0,
                "submitted_count": 0,
                "avg_score": None,
                "max_score": None,
                "min_score": None,
                "pass_count": 0,
                "pass_rate": None,
                "score_distribution": [],
            }

        scores = [s.total_score for s in sessions if s.total_score is not None]
        submitted_count = len(scores)

        if not scores:
            avg_score = None
            max_score = None
            min_score = None
        else:
            avg_score = round(sum(scores) / len(scores), 1)
            max_score = max(scores)
            min_score = min(scores)

        pass_count = sum(1 for s in scores if s >= exam.pass_score) if scores else 0
        pass_rate = round(pass_count / submitted_count * 100, 1) if submitted_count > 0 else None

        # 分数段分布
        distribution = _calculate_distribution(scores, exam.total_score)

        return {
            "exam_id": exam.id,
            "exam_name": exam.name,
            "total_students": db.query(ExamSession).filter(ExamSession.exam_id == exam_id).count(),
            "submitted_count": submitted_count,
            "avg_score": avg_score,
            "max_score": max_score,
            "min_score": min_score,
            "pass_count": pass_count,
            "pass_rate": pass_rate,
            "score_distribution": distribution,
        }

    @staticmethod
    def export_scores(db: Session, exam_id: int) -> Optional[bytes]:
        """导出成绩 Excel"""
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        sessions = db.query(ExamSession).filter(ExamSession.exam_id == exam_id).all()

        headers = ["序号", "用户名", "姓名", "班级", "得分", "状态", "用时(秒)", "提交时间"]
        rows = []
        for idx, session in enumerate(sessions, 1):
            user = db.query(User).filter(User.id == session.user_id).first()
            class_name = ""
            if user and user.class_id:
                cls = db.query(Class).filter(Class.id == user.class_id).first()
                class_name = cls.name if cls else ""

            status_map = {
                "not_started": "未开始",
                "in_progress": "答题中",
                "submitted": "已提交",
                "force_submitted": "强制提交",
                "auto_submitted": "自动提交",
            }

            rows.append([
                idx,
                user.username if user else "",
                user.name if user else "",
                class_name,
                session.total_score if session.total_score is not None else "",
                status_map.get(session.status, session.status),
                session.time_used or "",
                session.submit_time.strftime("%Y-%m-%d %H:%M:%S") if session.submit_time else "",
            ])

        return create_score_export(exam.name, headers, rows)


def _calculate_distribution(scores: List[int], total_score: int) -> list:
    """计算分数段分布"""
    if not scores or total_score <= 0:
        return []

    # 定义分数段
    ranges = [
        (0, total_score * 0.6, "不及格"),
        (total_score * 0.6, total_score * 0.7, "及格"),
        (total_score * 0.7, total_score * 0.8, "中等"),
        (total_score * 0.8, total_score * 0.9, "良好"),
        (total_score * 0.9, total_score + 1, "优秀"),
    ]

    distribution = []
    for low, high, label in ranges:
        count = sum(1 for s in scores if low <= s < high)
        distribution.append({
            "label": label,
            "range": f"{int(low)}-{int(high - 1)}" if high <= total_score else f"{int(low)}-{total_score}",
            "count": count,
            "percentage": round(count / len(scores) * 100, 1),
        })

    return distribution
