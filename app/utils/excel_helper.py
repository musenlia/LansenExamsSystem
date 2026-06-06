# -*- coding: utf-8 -*-
"""openpyxl Excel 模板定义与读写工具"""

import io
from typing import List, Dict, Optional, Tuple
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill


# ============================================================
# 样式定义
# ============================================================

_header_font = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
_header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
_header_alignment = Alignment(horizontal="center", vertical="center")
_cell_alignment = Alignment(vertical="center", wrap_text=True)
_thin_border = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


def _apply_header_style(ws, row: int, col_count: int) -> None:
    """应用表头样式"""
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = _header_font
        cell.fill = _header_fill
        cell.alignment = _header_alignment
        cell.border = _thin_border


def _apply_cell_style(ws, row: int, col_count: int) -> None:
    """应用单元格样式"""
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row, column=col)
        cell.alignment = _cell_alignment
        cell.border = _thin_border


# ============================================================
# 用户导入模板
# ============================================================

USER_IMPORT_HEADERS = ["username", "name", "password", "role", "class_name"]
USER_IMPORT_HEADER_LABELS = ["登录用户名", "真实姓名", "登录密码", "角色(管理员/学生)", "班级名称"]

# 中文字段映射
ROLE_CN_MAP = {"管理员": "admin", "学生": "student", "admin": "admin", "student": "student"}


def create_user_import_template() -> bytes:
    """
    创建用户导入模板 Excel

    Returns:
        Excel 文件字节数据
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "用户导入模板"

    # 写入表头标签行
    for col, label in enumerate(USER_IMPORT_HEADER_LABELS, 1):
        ws.cell(row=1, column=col, value=label)
    _apply_header_style(ws, 1, len(USER_IMPORT_HEADER_LABELS))

    # 写入示例数据
    examples = [
        ["zhangsan", "张三", "123456", "学生", "默认班级"],
        ["lisi", "李四", "123456", "学生", "2026年春季班"],
    ]
    for row_idx, example in enumerate(examples, 2):
        for col_idx, value in enumerate(example, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
        _apply_cell_style(ws, row_idx, len(example))

    # 设置列宽
    col_widths = [20, 20, 15, 20, 20]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def parse_user_import(file_data: bytes) -> Tuple[List[Dict], List[str]]:
    """
    解析用户导入 Excel 文件

    Args:
        file_data: Excel 文件字节数据

    Returns:
        (成功数据列表, 错误信息列表)
    """
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(file_data))
    ws = wb.active

    success_data: List[Dict] = []
    errors: List[str] = []

    # 读取表头，判断是标签行还是字段名行
    headers = []
    for col in range(1, ws.max_column + 1):
        val = ws.cell(row=1, column=col).value
        if val:
            headers.append(str(val).strip())

    # 判断表头类型
    if headers == USER_IMPORT_HEADER_LABELS:
        header_map = {label: field for label, field in zip(USER_IMPORT_HEADER_LABELS, USER_IMPORT_HEADERS)}
    elif all(h in USER_IMPORT_HEADERS for h in headers):
        header_map = {h: h for h in headers}
    else:
        return [], ["表头格式不正确，请使用模板导出的格式"]

    # 逐行解析
    for row_idx in range(2, ws.max_row + 1):
        row_data = {}
        for col_idx, header in enumerate(headers):
            cell_value = ws.cell(row=row_idx, column=col_idx + 1).value
            field = header_map.get(header)
            if field:
                row_data[field] = str(cell_value).strip() if cell_value is not None else ""

        # 校验必填字段
        username = row_data.get("username", "")
        name = row_data.get("name", "")
        password = row_data.get("password", "")
        role_raw = row_data.get("role", "student")
        # 兼容中文角色名
        role = ROLE_CN_MAP.get(role_raw, "student")

        if not username:
            errors.append(f"第{row_idx}行：用户名不能为空")
            continue
        if not name:
            errors.append(f"第{row_idx}行：姓名不能为空")
            continue
        if not password:
            errors.append(f"第{row_idx}行：密码不能为空")
            continue
        if role not in ("admin", "student"):
            errors.append(f"第{row_idx}行：角色必须为 管理员/学生（或 admin/student）")
            continue

        success_data.append({
            "username": username,
            "name": name,
            "password": password,
            "role": role,
            "class_name": row_data.get("class_name", ""),
        })

    return success_data, errors


# ============================================================
# 题目导入模板
# ============================================================

QUESTION_IMPORT_HEADERS = ["type", "content", "options", "answer", "score", "difficulty", "category_name", "analysis", "fill_match_mode"]
QUESTION_IMPORT_HEADER_LABELS = ["题型", "题目内容", "选项", "正确答案", "分值", "难度", "分类名称", "解析", "匹配模式"]

# 中文题型/难度/匹配模式映射
TYPE_CN_MAP = {
    "单选题": "single", "多选题": "multiple", "判断题": "judge", "填空题": "fill",
    "single": "single", "multiple": "multiple", "judge": "judge", "fill": "fill",
}
DIFFICULTY_CN_MAP = {
    "简单": "easy", "中等": "medium", "困难": "hard",
    "easy": "easy", "medium": "medium", "hard": "hard",
}
MATCH_MODE_CN_MAP = {
    "精确匹配": "exact", "包含匹配": "contain",
    "exact": "exact", "contain": "contain",
}


def create_question_import_template() -> bytes:
    """
    创建题目导入模板 Excel

    Returns:
        Excel 文件字节数据
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "题目导入模板"

    # 写入表头
    for col, label in enumerate(QUESTION_IMPORT_HEADER_LABELS, 1):
        ws.cell(row=1, column=col, value=label)
    _apply_header_style(ws, 1, len(QUESTION_IMPORT_HEADER_LABELS))

    # 写入填写说明行（浅灰背景）
    hints = [
        "填：单选题/多选题/判断题/填空题",
        "必填",
        "选择题填A:内容;B:内容，判断题/填空题留空",
        "单选填A，多选填A,B,C，判断填对/错，填空填答案",
        "数字，默认2",
        "填：简单/中等/困难",
        "填分类名称，不存在会自动创建",
        "选填",
        "仅填空题：精确匹配/包含匹配",
    ]
    hint_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    hint_font = Font(name="微软雅黑", size=9, color="666666", italic=True)
    for col, hint in enumerate(hints, 1):
        cell = ws.cell(row=2, column=col, value=hint)
        cell.fill = hint_fill
        cell.font = hint_font
        cell.alignment = _cell_alignment
        cell.border = _thin_border

    # 示例数据（全中文，与模板表头一致）
    examples = [
        ["单选题", "教育学的研究对象是？", "A:教育现象;B:教育方针;C:教育政策;D:教育理论", "A", 2, "简单", "高等教育学", "教育学是研究教育现象和教育问题的科学", ""],
        ["多选题", "以下哪些属于教育的基本要素？", "A:教育者;B:受教育者;C:教育内容;D:教育手段", "A,B,C,D", 4, "中等", "高等教育学", "", ""],
        ["判断题", "教育起源于劳动。", "", "对", 2, "简单", "高等教育学", "劳动起源说是马克思主义的教育起源观", ""],
        ["填空题", "教育的三大功能是___、___、___.", "", "本体功能,社会功能,文化功能", 6, "困难", "高等教育学", "", "包含匹配"],
    ]
    for row_idx, example in enumerate(examples, 3):
        for col_idx, value in enumerate(example, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
        _apply_cell_style(ws, row_idx, len(example))

    # 设置列宽
    col_widths = [15, 30, 35, 25, 8, 12, 15, 25, 15]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def parse_question_import(file_data: bytes) -> Tuple[List[Dict], List[str]]:
    """
    解析题目导入 Excel 文件

    Args:
        file_data: Excel 文件字节数据

    Returns:
        (成功数据列表, 错误信息列表)
    """
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(file_data))
    ws = wb.active

    success_data: List[Dict] = []
    errors: List[str] = []

    headers = []
    for col in range(1, ws.max_column + 1):
        val = ws.cell(row=1, column=col).value
        if val:
            headers.append(str(val).strip())

    # 判断表头类型
    if headers == QUESTION_IMPORT_HEADER_LABELS:
        header_map = {label: field for label, field in zip(QUESTION_IMPORT_HEADER_LABELS, QUESTION_IMPORT_HEADERS)}
    elif all(h in QUESTION_IMPORT_HEADERS for h in headers):
        header_map = {h: h for h in headers}
    else:
        return [], ["表头格式不正确，请使用模板导出的格式"]

    for row_idx in range(2, ws.max_row + 1):
        row_data = {}
        for col_idx, header in enumerate(headers):
            cell_value = ws.cell(row=row_idx, column=col_idx + 1).value
            field = header_map.get(header)
            if field:
                row_data[field] = str(cell_value).strip() if cell_value is not None else ""

        # 跳过说明行（以"填："开头的行）
        type_raw = row_data.get("type", "")
        if type_raw.startswith("填：") or type_raw.startswith("填:"):
            continue

        # 中英文题型映射
        q_type = TYPE_CN_MAP.get(type_raw, "")
        if not q_type:
            # 不是有效题型，可能是说明行或空行
            if type_raw:
                errors.append(f"第{row_idx}行：题型填写有误，请填写 单选题/多选题/判断题/填空题")
            continue

        content = row_data.get("content", "")
        answer = row_data.get("answer", "")

        if not content:
            errors.append(f"第{row_idx}行：题目内容不能为空")
            continue
        if not answer:
            errors.append(f"第{row_idx}行：正确答案不能为空")
            continue

        # 解析选项
        options_raw = row_data.get("options", "")
        options = _parse_options(options_raw, q_type, answer) if options_raw else None

        # 判断题：如果没有选项则自动生成，并规范化 answer 为 true/false
        if q_type == "judge":
            if not options:
                is_correct_true = answer in ("对", "正确", "true", "True", "√")
                options = [
                    {"label": "true", "content": "正确", "is_correct": is_correct_true},
                    {"label": "false", "content": "错误", "is_correct": not is_correct_true},
                ]
            # 规范化 answer
            if answer in ("对", "正确", "true", "True", "√"):
                answer = "true"
            elif answer in ("错", "错误", "false", "False", "×"):
                answer = "false"

        # 分值默认
        try:
            score = int(row_data.get("score", "2") or "2")
        except ValueError:
            score = 2

        # 中文难度映射
        difficulty_raw = row_data.get("difficulty", "medium") or "medium"
        difficulty = DIFFICULTY_CN_MAP.get(difficulty_raw, "medium")

        # 中文匹配模式映射
        match_mode_raw = row_data.get("fill_match_mode", "") or None
        fill_match_mode = MATCH_MODE_CN_MAP.get(match_mode_raw, match_mode_raw) if match_mode_raw else None

        success_data.append({
            "type": q_type,
            "content": content,
            "options": options,
            "answer": answer,
            "score": score,
            "difficulty": difficulty,
            "category_name": row_data.get("category_name", ""),
            "analysis": row_data.get("analysis", ""),
            "fill_match_mode": fill_match_mode,
        })

    return success_data, errors


def _parse_options(options_str: str, q_type: str = "", answer: str = "") -> Optional[list]:
    """
    解析选项字符串为列表格式（与前端/数据库一致）

    支持格式：
    1. JSON格式: [{"label":"A","content":"选项A","is_correct":false}, ...]
    2. 分号格式: A:选项A;B:选项B（根据 answer 自动推算 is_correct）

    Args:
        options_str: 选项字符串
        q_type: 题型（用于推算 is_correct）
        answer: 正确答案（用于推算 is_correct）

    Returns:
        选项列表 [{label, content, is_correct}, ...] 或 None
    """
    if not options_str:
        return None

    options_str = options_str.strip()

    # 尝试 JSON 格式
    if options_str.startswith("["):
        import json
        try:
            parsed = json.loads(options_str)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # 分号格式 → 转为 list
    result = []
    parts = options_str.split(";")
    # 解析出正确答案的 label 集合
    correct_labels = set()
    if answer:
        for a in answer.split(","):
            a = a.strip()
            if a:
                correct_labels.add(a)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            key, value = part.split(":", 1)
        elif "：" in part:
            key, value = part.split("：", 1)
        else:
            continue
        label = key.strip()
        content = value.strip()
        is_correct = label in correct_labels
        result.append({"label": label, "content": content, "is_correct": is_correct})

    return result if result else None


# ============================================================
# 用户数据导出（与导入模板格式完全一致，可直接重新导入）
# ============================================================

def export_users_to_excel(users_data: list) -> bytes:
    """
    将用户列表导出为 Excel，列格式与用户导入模板完全一致。

    Args:
        users_data: [{"username", "name", "role", "class_name"}, ...]
    Returns:
        Excel 字节数据
    """
    # 角色反向映射（英文→中文）
    ROLE_CN_REVERSE = {"admin": "管理员", "teacher": "教师", "student": "学生"}

    wb = Workbook()
    ws = wb.active
    ws.title = "用户数据"

    # 写入表头（与导入模板完全一致）
    for col, label in enumerate(USER_IMPORT_HEADER_LABELS, 1):
        ws.cell(row=1, column=col, value=label)
    _apply_header_style(ws, 1, len(USER_IMPORT_HEADER_LABELS))

    # 写入数据行
    for row_idx, u in enumerate(users_data, 2):
        role_cn = ROLE_CN_REVERSE.get(u.get("role", "student"), "学生")
        row = [
            u.get("username", ""),
            u.get("name", ""),
            "（请填写新密码）",      # 安全考虑：密码哈希不可逆，提示用户重新填写
            role_cn,
            u.get("class_name", ""),
        ]
        for col_idx, value in enumerate(row, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
        _apply_cell_style(ws, row_idx, len(row))

    # 设置列宽（与模板一致）
    col_widths = [20, 20, 20, 20, 20]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 题库数据导出（与导入模板格式完全一致，可直接重新导入）
# ============================================================

def export_questions_to_excel(questions_data: list) -> bytes:
    """
    将题目列表导出为 Excel，列格式与题目导入模板完全一致。

    Args:
        questions_data: [{"type","content","options","answer","score","difficulty","category_name","analysis","fill_match_mode"}, ...]
    Returns:
        Excel 字节数据
    """
    import json as _json

    # 反向映射（英文→中文）
    TYPE_CN_REVERSE = {"single": "单选题", "multiple": "多选题", "judge": "判断题", "fill": "填空题"}
    DIFF_CN_REVERSE = {"easy": "简单", "medium": "中等", "hard": "困难"}
    MATCH_CN_REVERSE = {"exact": "精确匹配", "contain": "包含匹配"}
    JUDGE_ANSWER_REVERSE = {"true": "对", "false": "错"}

    wb = Workbook()
    ws = wb.active
    ws.title = "题库数据"

    # 写入表头（与导入模板完全一致）
    for col, label in enumerate(QUESTION_IMPORT_HEADER_LABELS, 1):
        ws.cell(row=1, column=col, value=label)
    _apply_header_style(ws, 1, len(QUESTION_IMPORT_HEADER_LABELS))

    for row_idx, q in enumerate(questions_data, 2):
        q_type = q.get("type", "single")
        options_raw = q.get("options")
        answer_raw = q.get("answer", "")

        # 将 options list 转回 "A:内容;B:内容" 格式
        options_str = ""
        if options_raw:
            if isinstance(options_raw, str):
                try:
                    options_raw = _json.loads(options_raw)
                except Exception:
                    options_raw = []
            if isinstance(options_raw, list) and q_type != "judge":
                options_str = ";".join(
                    f"{opt.get('label', '')}:{opt.get('content', '')}"
                    for opt in options_raw
                    if opt.get("label") and opt.get("content")
                )

        # 判断题答案反向映射
        if q_type == "judge":
            answer_str = JUDGE_ANSWER_REVERSE.get(str(answer_raw).lower(), answer_raw)
        else:
            answer_str = answer_raw

        row = [
            TYPE_CN_REVERSE.get(q_type, q_type),
            q.get("content", ""),
            options_str,
            answer_str,
            q.get("score", 2),
            DIFF_CN_REVERSE.get(q.get("difficulty", "medium"), "中等"),
            q.get("category_name", ""),
            q.get("analysis", "") or "",
            MATCH_CN_REVERSE.get(q.get("fill_match_mode", "") or "", "") if q_type == "fill" else "",
        ]
        for col_idx, value in enumerate(row, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
        _apply_cell_style(ws, row_idx, len(row))

    # 设置列宽（与模板一致）
    col_widths = [15, 30, 35, 25, 8, 12, 15, 25, 15]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 成绩导出
# ============================================================


def create_score_export(
    exam_name: str,
    headers: List[str],
    rows: List[List],
) -> bytes:
    """
    创建成绩导出 Excel

    Args:
        exam_name: 考试名称
        headers: 表头列表
        rows: 数据行列表

    Returns:
        Excel 文件字节数据
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "成绩导出"

    # 标题行
    ws.cell(row=1, column=1, value=f"{exam_name} - 成绩单")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    title_cell = ws.cell(row=1, column=1)
    title_cell.font = Font(name="微软雅黑", size=14, bold=True)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")

    # 表头
    for col, header in enumerate(headers, 1):
        ws.cell(row=2, column=col, value=header)
    _apply_header_style(ws, 2, len(headers))

    # 数据行
    for row_idx, row_data in enumerate(rows, 3):
        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
        _apply_cell_style(ws, row_idx, len(headers))

    # 自动列宽（从第2行表头开始计算，避免合并单元格问题）
    from openpyxl.utils import get_column_letter
    for col in range(1, len(headers) + 1):
        max_len = max(
            len(str(ws.cell(row=r, column=col).value or ""))
            for r in range(2, len(rows) + 3)
        )
        ws.column_dimensions[get_column_letter(col)].width = min(max_len + 4, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 考试备份导出（多 Sheet，含隐藏 JSON Sheet 用于恢复）
# ============================================================

def export_exam_backup_to_excel(backup_data: dict) -> bytes:
    """
    将考试备份数据导出为多 Sheet Excel 文件。

    Sheet 布局：
      - {考试名}-信息：基本信息（每行一个字段）
      - {考试名}-题目：所有题目明细
      - {考试名}-成绩：每位考生总分
      - {考试名}-答卷：每位考生每道题的作答情况
      - _backup_json（隐藏）：原始 JSON，用于程序恢复
    """
    import json as _json
    from openpyxl.utils import get_column_letter

    TYPE_CN = {"single": "单选题", "multiple": "多选题", "judge": "判断题", "fill": "填空题"}
    DIFF_CN = {"easy": "简单", "medium": "中等", "hard": "困难"}
    JUDGE_ANSWER_CN = {"true": "对", "false": "错"}

    exams = backup_data.get("exams", [])

    if not exams:
        # 没有考试数据时，直接返回只有备份JSON的文件（不隐藏唯一Sheet）
        wb = Workbook()
        ws_json = wb.active
        ws_json.title = "_backup_json"
        json_str = _json.dumps(backup_data, ensure_ascii=False)
        chunk_size = 30000
        for i, start in enumerate(range(0, len(json_str), chunk_size), 1):
            ws_json.cell(row=i, column=1, value=json_str[start:start + chunk_size])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.getvalue()

    wb = Workbook()
    wb.remove(wb.active)  # 删除默认空Sheet

    for exam_data in exams:
        exam_name_raw = exam_data.get("name", "考试")
        # Sheet名称不能超过31字符，去掉非法字符
        safe_name = exam_name_raw[:20].replace("/", "").replace("\\", "").replace("*", "").replace("?", "").replace("[", "").replace("]", "").replace(":", "")

        # ── Sheet1: 考试信息 ──────────────────────────────────
        ws_info = wb.create_sheet(title=f"{safe_name}-信息")
        info_rows = [
            ["字段", "值"],
            ["考试名称", exam_data.get("name", "")],
            ["考试说明", exam_data.get("description") or ""],
            ["开始时间", exam_data.get("start_time") or ""],
            ["考试时长(分钟)", exam_data.get("duration", "")],
            ["总分", exam_data.get("total_score", "")],
            ["及格分", exam_data.get("pass_score", "")],
            ["考试模式", exam_data.get("mode", "")],
            ["题目随机", "是" if exam_data.get("shuffle_question") else "否"],
            ["选项随机", "是" if exam_data.get("shuffle_option") else "否"],
            ["注意事项", exam_data.get("notice") or ""],
        ]
        classes = exam_data.get("classes", [])
        class_names = "、".join(c.get("name", "") for c in classes)
        info_rows.append(["关联班级", class_names])

        for r_idx, row in enumerate(info_rows, 1):
            for c_idx, val in enumerate(row, 1):
                cell = ws_info.cell(row=r_idx, column=c_idx, value=val)
                if r_idx == 1:
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill(fill_type="solid", fgColor="4472C4")
        ws_info.column_dimensions["A"].width = 20
        ws_info.column_dimensions["B"].width = 50

        # ── Sheet2: 题目列表 ──────────────────────────────────
        ws_q = wb.create_sheet(title=f"{safe_name}-题目")
        q_headers = ["序号", "题型", "题目内容", "选项", "正确答案", "分值", "难度", "分类"]
        for c_idx, h in enumerate(q_headers, 1):
            cell = ws_q.cell(row=1, column=c_idx, value=h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(fill_type="solid", fgColor="4472C4")

        questions = exam_data.get("questions", [])
        for q_idx, q in enumerate(questions, 2):
            options_raw = q.get("options")
            options_str = ""
            if options_raw:
                if isinstance(options_raw, str):
                    try:
                        options_raw = _json.loads(options_raw)
                    except Exception:
                        options_raw = []
                if isinstance(options_raw, list) and q.get("type") != "judge":
                    options_str = "；".join(
                        f"{opt.get('label', '')}:{opt.get('content', '')}"
                        for opt in options_raw
                    )
            answer_raw = q.get("answer", "")
            if q.get("type") == "judge":
                answer_str = JUDGE_ANSWER_CN.get(str(answer_raw).lower(), answer_raw)
            else:
                answer_str = answer_raw
            row = [
                q.get("order_num", q_idx - 1),
                TYPE_CN.get(q.get("type", "single"), q.get("type", "")),
                q.get("content", ""),
                options_str,
                answer_str,
                q.get("exam_score", q.get("score", 2)),
                DIFF_CN.get(q.get("difficulty", "medium"), "中等"),
                q.get("category_name", "") or "",
            ]
            for c_idx, val in enumerate(row, 1):
                ws_q.cell(row=q_idx, column=c_idx, value=val)
        col_widths_q = [6, 10, 40, 40, 15, 6, 8, 15]
        for i, w in enumerate(col_widths_q, 1):
            ws_q.column_dimensions[get_column_letter(i)].width = w

        # ── Sheet3: 成绩汇总 ──────────────────────────────────
        ws_score = wb.create_sheet(title=f"{safe_name}-成绩")
        score_headers = ["序号", "用户名", "姓名", "班级", "得分", "及格分", "是否及格", "用时(秒)", "交卷时间"]
        for c_idx, h in enumerate(score_headers, 1):
            cell = ws_score.cell(row=1, column=c_idx, value=h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(fill_type="solid", fgColor="4472C4")

        students = exam_data.get("student_results", [])
        for s_idx, s in enumerate(students, 2):
            row = [
                s_idx - 1,
                s.get("username", ""),
                s.get("name", ""),
                s.get("class_name") or "",
                s.get("score"),
                s.get("pass_score"),
                "是" if s.get("is_passed") else ("否" if s.get("is_passed") is False else ""),
                s.get("duration_seconds", 0),
                s.get("submit_time") or "",
            ]
            for c_idx, val in enumerate(row, 1):
                ws_score.cell(row=s_idx, column=c_idx, value=val)
        col_widths_s = [6, 15, 15, 15, 8, 8, 8, 10, 22]
        for i, w in enumerate(col_widths_s, 1):
            ws_score.column_dimensions[get_column_letter(i)].width = w

        # ── Sheet4: 答卷明细 ──────────────────────────────────
        ws_detail = wb.create_sheet(title=f"{safe_name}-答卷")
        detail_headers = ["姓名", "用户名", "班级", "题号", "题型", "题目", "正确答案", "考生答案", "得分", "满分", "是否正确"]
        for c_idx, h in enumerate(detail_headers, 1):
            cell = ws_detail.cell(row=1, column=c_idx, value=h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(fill_type="solid", fgColor="4472C4")

        detail_row_num = 2
        for s in students:
            for a_idx, ans in enumerate(s.get("answers", []), 1):
                answer_val = ans.get("student_answer", "")
                correct_val = ans.get("correct_answer", "")
                if ans.get("type") == "judge":
                    answer_val = JUDGE_ANSWER_CN.get(str(answer_val).lower(), answer_val) if answer_val else ""
                    correct_val = JUDGE_ANSWER_CN.get(str(correct_val).lower(), correct_val) if correct_val else ""
                row = [
                    s.get("name", ""),
                    s.get("username", ""),
                    s.get("class_name") or "",
                    a_idx,
                    TYPE_CN.get(ans.get("type", ""), ans.get("type", "")),
                    ans.get("content", ""),
                    correct_val,
                    answer_val,
                    ans.get("score"),
                    ans.get("max_score"),
                    "正确" if ans.get("is_correct") else ("错误" if ans.get("is_correct") is False else ""),
                ]
                for c_idx, val in enumerate(row, 1):
                    ws_detail.cell(row=detail_row_num, column=c_idx, value=val)
                detail_row_num += 1
        col_widths_d = [12, 15, 12, 6, 8, 40, 15, 15, 6, 6, 8]
        for i, w in enumerate(col_widths_d, 1):
            ws_detail.column_dimensions[get_column_letter(i)].width = w

    # ── 隐藏 Sheet: 原始 JSON 数据（供程序恢复使用） ──────────
    ws_json = wb.create_sheet(title="_backup_json")
    ws_json.sheet_state = "hidden"
    json_str = _json.dumps(backup_data, ensure_ascii=False)
    # 按 30000 字符分块写入（Excel 单格字符上限 32767）
    chunk_size = 30000
    for i, start in enumerate(range(0, len(json_str), chunk_size), 1):
        ws_json.cell(row=i, column=1, value=json_str[start:start + chunk_size])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def read_exam_backup_from_excel(file_content: bytes) -> Tuple[bool, str, dict]:
    """
    从考试备份 Excel 文件中读取备份数据（从隐藏 Sheet _backup_json 提取 JSON）。
    返回 (success, message, backup_data_dict)
    """
    import json as _json
    from openpyxl import load_workbook

    try:
        wb = load_workbook(filename=io.BytesIO(file_content), read_only=True, data_only=True)
    except Exception as e:
        return False, f"无法读取 Excel 文件: {e}", {}

    if "_backup_json" not in wb.sheetnames:
        return False, "备份文件格式不正确，缺少 _backup_json 数据（此文件可能不是考试备份文件）", {}

    ws = wb["_backup_json"]
    json_parts = []
    for row in ws.iter_rows(min_row=1, values_only=True):
        val = row[0] if row else None
        if val is not None:
            json_parts.append(str(val))
    json_str = "".join(json_parts)
    wb.close()

    try:
        data = _json.loads(json_str)
    except _json.JSONDecodeError as e:
        return False, f"备份数据解析失败: {e}", {}

    if not isinstance(data, dict) or "exams" not in data:
        return False, "备份数据结构不正确，缺少 exams 字段", {}

    return True, "解析成功", data
