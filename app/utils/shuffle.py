# -*- coding: utf-8 -*-
"""Fisher-Yates 洗牌算法 - 题目乱序 + 选项乱序"""

import random
from typing import List, Optional


def fisher_yates_shuffle(items: List) -> List:
    """
    Fisher-Yates 洗牌算法（原地洗牌的副本版本）

    对列表进行均匀随机洗牌，返回新的打乱后的列表，
    不修改原始列表。

    Args:
        items: 待洗牌的列表

    Returns:
        打乱顺序后的新列表
    """
    shuffled = items.copy()
    n = len(shuffled)
    for i in range(n - 1, 0, -1):
        j = random.randint(0, i)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def generate_question_order(question_ids: List[int], shuffle: bool = True) -> List[int]:
    """
    生成题目乱序

    为考生生成独立的题目顺序。如果 shuffle=False，返回原始顺序。

    Args:
        question_ids: 原始题目ID列表
        shuffle: 是否打乱顺序

    Returns:
        打乱后的题目ID列表
    """
    if not shuffle:
        return question_ids.copy()
    return fisher_yates_shuffle(question_ids)


def generate_option_order(option_count: int, shuffle: bool = True) -> List[int]:
    """
    生成选项乱序

    为考生生成独立的选项顺序。返回的是选项索引列表。
    例如原始选项 [A, B, C, D]，乱序后可能变为 [2, 0, 3, 1]，
    表示显示顺序为 C, A, D, B。

    Args:
        option_count: 选项数量
        shuffle: 是否打乱顺序

    Returns:
        选项索引列表（乱序后的）
    """
    indices = list(range(option_count))
    if not shuffle:
        return indices
    return fisher_yates_shuffle(indices)


def get_shuffled_options(
    options: dict,
    option_order: Optional[List[int]] = None,
    shuffle: bool = False
) -> List[dict]:
    """
    根据乱序索引获取重排后的选项列表

    Args:
        options: 原始选项字典，如 {"A": "选项A", "B": "选项B", ...}
        option_order: 选项乱序索引，如 [2, 0, 3, 1]
        shuffle: 如果 option_order 为 None，是否自动生成乱序

    Returns:
        重排后的选项列表，如 [{"key": "C", "value": "选项C"}, ...]
    """
    if not options:
        return []

    # 将字典转为有序列表
    items = [{"key": k, "value": v} for k, v in options.items()]

    if option_order is None and shuffle:
        option_order = generate_option_order(len(items), shuffle=True)

    if option_order:
        # 按乱序索引重排
        return [items[i] for i in option_order if i < len(items)]

    return items
