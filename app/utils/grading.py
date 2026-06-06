# -*- coding: utf-8 -*-
"""自动评分引擎 - 单选/多选/判断/填空 评分"""

from typing import Optional, Tuple


def grade_single_choice(user_answer: str, correct_answer: str) -> bool:
    """
    单选题评分 - 精确匹配

    Args:
        user_answer: 考生答案（如 "A"）
        correct_answer: 正确答案（如 "A"）

    Returns:
        是否正确
    """
    if not user_answer or not correct_answer:
        return False
    return user_answer.strip().upper() == correct_answer.strip().upper()


def grade_multiple_choice(user_answer: str, correct_answer: str) -> Tuple[bool, bool]:
    """
    多选题评分 - 排序后匹配

    部分正确策略：完全正确给满分，否则0分。
    如果需要部分得分，可在外层调用中处理。

    Args:
        user_answer: 考生答案（如 "A,C,D" 或 "ACD"）
        correct_answer: 正确答案（如 "A,C,D" 或 "ACD"）

    Returns:
        (是否完全正确, 是否部分正确)
    """
    if not user_answer or not correct_answer:
        return False, False

    # 解析用户答案：支持逗号分隔或直接连接
    user_set = _parse_multiple_answer(user_answer)
    correct_set = _parse_multiple_answer(correct_answer)

    if not user_set or not correct_set:
        return False, False

    is_fully_correct = user_set == correct_set
    is_partial = bool(user_set & correct_set) and not is_fully_correct

    return is_fully_correct, is_partial


def grade_judge(user_answer: str, correct_answer: str) -> bool:
    """
    判断题评分 - 布尔匹配

    Args:
        user_answer: 考生答案（如 "对"/"正确"/"true"/"T"）
        correct_answer: 正确答案（如 "对"/"正确"/"true"/"T"）

    Returns:
        是否正确
    """
    if not user_answer or not correct_answer:
        return False

    def normalize_judge(val: str) -> Optional[bool]:
        """将判断题答案标准化为布尔值"""
        v = val.strip().upper()
        if v in ("对", "正确", "TRUE", "T", "YES", "Y", "1"):
            return True
        if v in ("错", "错误", "FALSE", "F", "NO", "N", "0"):
            return False
        return None

    user_norm = normalize_judge(user_answer)
    correct_norm = normalize_judge(correct_answer)

    if user_norm is None or correct_norm is None:
        # 无法识别的答案，回退到字符串匹配
        return user_answer.strip().upper() == correct_answer.strip().upper()

    return user_norm == correct_norm


def grade_fill(
    user_answer: str,
    correct_answer: str,
    match_mode: str = "exact"
) -> bool:
    """
    填空题评分 - 关键词匹配

    Args:
        user_answer: 考生答案
        correct_answer: 正确答案
        match_mode: 匹配模式
            - exact: 精确匹配（忽略前后空格）
            - contain: 包含匹配（正确答案在考生答案中）

    Returns:
        是否正确
    """
    if not user_answer or not correct_answer:
        return False

    user = user_answer.strip()
    correct = correct_answer.strip()

    if match_mode == "exact":
        return user == correct
    elif match_mode == "contain":
        return correct in user
    else:
        return user == correct


def grade_question(
    question_type: str,
    user_answer: str,
    correct_answer: str,
    fill_match_mode: Optional[str] = None,
    score: int = 0,
) -> Tuple[bool, int]:
    """
    通用评分函数

    Args:
        question_type: 题型 (single/multiple/judge/fill)
        user_answer: 考生答案
        correct_answer: 正确答案
        fill_match_mode: 填空匹配模式（仅填空题需要）
        score: 该题分值

    Returns:
        (是否正确, 得分)
    """
    is_correct = False

    if question_type == "single":
        is_correct = grade_single_choice(user_answer, correct_answer)
    elif question_type == "multiple":
        is_correct, _ = grade_multiple_choice(user_answer, correct_answer)
    elif question_type == "judge":
        is_correct = grade_judge(user_answer, correct_answer)
    elif question_type == "fill":
        mode = fill_match_mode or "exact"
        is_correct = grade_fill(user_answer, correct_answer, mode)
    else:
        return False, 0

    earned_score = score if is_correct else 0
    return is_correct, earned_score


def _parse_multiple_answer(answer: str) -> set:
    """
    解析多选题答案为集合

    支持 "A,C,D" 和 "ACD" 两种格式

    Args:
        answer: 答案字符串

    Returns:
        选项字母集合
    """
    answer = answer.strip().upper()
    if "," in answer or "，" in answer:
        # 逗号分隔格式
        parts = answer.replace("，", ",").split(",")
        return {p.strip() for p in parts if p.strip()}
    else:
        # 直接连接格式，如 "ACD"
        return {c for c in answer if c.isalpha()}
