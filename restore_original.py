#!/usr/bin/env python3
import os

js_file = r"e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js"

# 读取文件
with open(js_file, 'rb') as f:
    content = f.read()

# 定义要替换的字符串（UTF-8编码）
# 先查找SVG内容并替换回原始文本
old_str = '''<svg width="48" height="40" viewBox="0 0 48 40" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M6 36V20L24 12L42 20V36H30V28L24 24L18 28V36H6Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M6 28H18M30 28H42" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
<path d="M12 8L24 2L36 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M24 2V14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
<path d="M16 8V14M32 8V14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg><span style="margin-left:8px;font-weight:600;">Lansen</span>'''.encode('utf-8')

new_str = '教师培训考试管理系统'.encode('utf-8')

# 检查字符串是否存在
if old_str in content:
    # 替换字符串
    new_content = content.replace(old_str, new_str)
    # 写入文件
    with open(js_file, 'wb') as f:
        f.write(new_content)
    print("已恢复为原始文本！")
    print(f"替换后: {new_str.decode('utf-8')}")
else:
    print("未找到SVG内容，尝试查找其他可能的内容...")
    # 尝试查找其他可能的字符串
    other_strings = [
        '代码即江湖 Lansen 见乾坤。'.encode('utf-8'),
        '代码即江湖，Lansen 见乾坤。'.encode('utf-8')
    ]
    for s in other_strings:
        if s in content:
            new_content = content.replace(s, new_str)
            with open(js_file, 'wb') as f:
                f.write(new_content)
            print(f"找到并恢复: {s.decode('utf-8')}")
            break
    else:
        print("未找到任何需要恢复的字符串")
