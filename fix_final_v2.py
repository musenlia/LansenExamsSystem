# -*- coding: utf-8 -*-
"""
最终修复：只针对应用代码区域（第1100行之后）做括号平衡。
库代码中的 IIFE 模式如 }}})(tZ) 是正常的，不做修改。
"""
import re

JS_PATH = r"e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js"

with open(JS_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Only fix lines 1100+ (app code)
for line_idx in range(1099, len(lines)):
    line = lines[line_idx]
    
    # Check if this line is part of a string (template literals spanning lines)
    # Simple heuristic: if line has bracket imbalance, fix it
    
    # Count brackets with string awareness
    balance = 0
    in_string = False
    string_char = None
    escape = False
    chars = list(line)
    
    for i in range(len(chars)):
        ch = chars[i]
        
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
                if balance <= 0:
                    chars[i] = ''  # Remove extra closing bracket
                else:
                    balance -= 1
    
    fixed = ''.join(chars)
    if fixed != line:
        lines[line_idx] = fixed
        o = fixed.count("(")+fixed.count("{")+fixed.count("[")
        c = fixed.count(")")+fixed.count("}")+fixed.count("]")
        print(f"Line {line_idx+1}: removed {line.count(')')+line.count('}')+line.count(']') - (fixed.count(')')+fixed.count('}')+fixed.count(']'))} brackets, diff now {o-c}")

# Write
with open(JS_PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

# Verify
with open(JS_PATH, "r", encoding="utf-8") as f:
    content = f.read()

o_all = content.count("(") + content.count("{") + content.count("[")
c_all = content.count(")") + content.count("}") + content.count("]")
print(f"\nFull file: opens={o_all}, closes={c_all}, diff={o_all-c_all}")
if o_all == c_all:
    print("SUCCESS: Brackets perfectly balanced!")
else:
    # Show only app code lines still imbalanced
    all_lines = content.split("\n")
    for i, ln in enumerate(all_lines):
        if i >= 1099:
            d = ln.count("(")+ln.count("{")+ln.count("[") - (ln.count(")")+ln.count("}")+ln.count("]"))
            if d != 0:
                print(f"  Line {i+1}: diff={d:+d}")
