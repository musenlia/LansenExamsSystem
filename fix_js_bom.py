#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def remove_bom(file_path):
    """移除文件开头的BOM标记"""
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # 检查是否有BOM
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
        print(f"已移除 {file_path} 的BOM标记")
    
    # 写入文件
    with open(file_path, 'wb') as f:
        f.write(content)

if __name__ == '__main__':
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    remove_bom(js_path)
    print("修复完成")