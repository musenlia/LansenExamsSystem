#!/usr/bin/env python3
import os

js_file = r"e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js"

# 读取文件
with open(js_file, 'rb') as f:
    content = f.read()

# 定义要替换的字符串（UTF-8编码）
old_str = '代码即江湖 Lansen 见乾坤。'.encode('utf-8')

# 创建一个简约的书本+毕业帽图标SVG
logo_svg = '''<svg width="48" height="40" viewBox="0 0 48 40" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M6 36V20L24 12L42 20V36H30V28L24 24L18 28V36H6Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M6 28H18M30 28H42" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
<path d="M12 8L24 2L36 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M24 2V14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
<path d="M16 8V14M32 8V14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg><span style="margin-left:8px;font-weight:600;">Lansen</span>'''

new_str = logo_svg.encode('utf-8')

# 检查字符串是否存在
if old_str in content:
    # 替换字符串
    new_content = content.replace(old_str, new_str)
    # 写入文件
    with open(js_file, 'wb') as f:
        f.write(new_content)
    print("修改完成！")
    print("已将文本替换为图形Logo")
else:
    print("未找到目标字符串")
