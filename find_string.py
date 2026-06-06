#!/usr/bin/env python3
import os

js_file = r"e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js"

with open(js_file, 'rb') as f:
    content = f.read()

# 尝试用不同编码搜索
encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
target_str = '教师培训考试管理系统'

for encoding in encodings:
    try:
        target = target_str.encode(encoding)
        index = content.find(target)
        if index != -1:
            print(f"使用 {encoding} 编码找到字符串位置: 字节 {index}")
            # 显示前后各50个字节
            start = max(0, index - 50)
            end = min(len(content), index + len(target) + 50)
            print("\n上下文内容:")
            print("-" * 60)
            print(content[start:end].decode(encoding, errors='ignore'))
            print("-" * 60)
            break
    except:
        pass
else:
    print("未找到目标字符串")
