#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def search_exam_status():
    """搜索考试状态相关代码"""
    
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 搜索考试状态关键字
    keywords = ['ended', 'archived', '已结束', '已归档', 'published']
    
    print("=== 找到的考试状态相关内容 ===")
    print()
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for keyword in keywords:
            if keyword in line:
                print(f"第 {i+1} 行: {line[:200]}")
                print()
                break

if __name__ == '__main__':
    search_exam_status()