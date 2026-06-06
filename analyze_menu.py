#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def analyze_menu_structure():
    """分析菜单结构，找到安全的添加位置"""
    
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找菜单配置的模式
    keywords = ['题库管理', '考试管理', '成绩管理', '用户管理', '参数配置']
    
    print("=== 菜单结构分析 ===")
    print()
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for keyword in keywords:
            if keyword in line:
                # 显示上下文
                print(f"找到菜单项: '{keyword}'")
                print(f"行号: {i+1}")
                print("上下文:")
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    prefix = "->" if j == i else "   "
                    print(f"{prefix}[{j+1}] {lines[j][:100]}")
                print()
                break

if __name__ == '__main__':
    analyze_menu_structure()