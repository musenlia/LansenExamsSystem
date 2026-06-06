# -*- coding: utf-8 -*-
"""找到应用代码中多余的开括号位置"""
import re

JS_PATH = r"e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js"

with open(JS_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Focus on lines 1100+
# Track bracket balance across all app code lines
# When balance goes positive and stays positive, find where the extra opens are

# Simple approach: track balance across the whole app code
# and report when balance exceeds a threshold (indicating unmatched opens)

app_lines = lines[1099:]  # Lines 1100+
app_text = ''.join(app_lines)

balance = 0
in_string = False
string_char = None
escape = False
max_balance = 0
max_pos = 0

for i, ch in enumerate(app_text):
    if escape:
        escape = False
        continue
    if ch == '\\' and in_string:
        escape = True
        continue
    if ch in '"\'':
        if in_string and ch == string_char:
            in_string = False
        elif not in_string:
            in_string = True
            string_char = ch
        continue
    
    if not in_string:
        if ch in "({[":
            balance += 1
        elif ch in ")}]":
            balance -= 1
    
    if balance > max_balance:
        max_balance = balance
        max_pos = i

print(f"Max balance in app code: {max_balance} at position {max_pos}")
print(f"Final balance: {balance}")

# Show the area around max balance
ctx_start = max(0, max_pos - 60)
ctx_end = min(len(app_text), max_pos + 60)
print(f"\nContext around max balance:")
print(repr(app_text[ctx_start:ctx_end]))
