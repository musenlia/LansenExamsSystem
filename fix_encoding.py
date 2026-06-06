#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

def detect_and_fix_encoding(file_path):
    """检测并修复文件编码问题"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                # 检查是否有乱码特征
                if '瀛︿範' in content or '鍩硅' in content:
                    print(f"文件 {file_path} 使用 {encoding} 编码读取，包含乱码")
                    # 尝试转换为UTF-8
                    if encoding != 'utf-8':
                        with open(file_path, 'w', encoding='utf-8') as out_f:
                            out_f.write(content)
                        print(f"已将 {file_path} 转换为 UTF-8 编码")
                return True
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    
    print(f"无法检测文件 {file_path} 的编码")
    return False

def main():
    # 检查并修复HTML文件
    html_path = r'E:\ExamsSystem_2.0\app\static\index.html'
    if os.path.exists(html_path):
        detect_and_fix_encoding(html_path)
    
    # 检查并修复JavaScript文件
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    if os.path.exists(js_path):
        detect_and_fix_encoding(js_path)
    
    print("编码修复完成")

if __name__ == '__main__':
    main()