#!/usr/bin/env python3
import os

js_file = r"e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js"

# 读取文件
with open(js_file, 'rb') as f:
    content = f.read()

# 定义要替换的字符串（UTF-8编码）
old_str = '教师培训考试管理系统'.encode('utf-8')
new_str = '代码即江湖 Lansen 见乾坤。'.encode('utf-8')

# 检查字符串是否存在
if old_str in content:
    # 替换字符串
    new_content = content.replace(old_str, new_str)
    # 写入文件
    with open(js_file, 'wb') as f:
        f.write(new_content)
    print("修改完成！")
    print(f"替换前: {old_str.decode('utf-8')}")
    print(f"替换后: {new_str.decode('utf-8')}")
else:
    print("未找到目标字符串")
