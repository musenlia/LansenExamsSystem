#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def search_exam_list():
    """搜索考试列表页面相关代码"""
    
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 搜索考试列表相关的模式
    patterns = ['/api/exams', 'exams/', 'ExamList', '考试管理']
    
    print("=== 找到的考试列表相关内容 ===")
    print()
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for pattern in patterns:
            if pattern in line:
                print(f"第 {i+1} 行: {line[:200]}")
                # 显示上下文
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    prefix = "->" if j == i else "   "
                    print(f"{prefix}[{j+1}] {lines[j][:150]}")
                print()
                break

if __name__ == '__main__':
    search_exam_list()