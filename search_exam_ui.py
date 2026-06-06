#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def search_exam_operations():
    """搜索前端考试操作相关代码"""
    
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 搜索考试相关的操作关键字
    keywords = ['发布', '终止', '暂停', '恢复', '归档']
    
    print("=== 找到的考试操作相关内容 ===")
    print()
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for keyword in keywords:
            if keyword in line:
                print(f"第 {i+1} 行: {line[:150]}")
                # 显示上下文
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    prefix = "->" if j == i else "   "
                    print(f"{prefix}[{j+1}] {lines[j][:120]}")
                print()
                break

if __name__ == '__main__':
    search_exam_operations()