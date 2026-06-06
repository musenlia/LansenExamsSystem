#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def find_menu_items():
    """查找菜单相关内容"""
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 搜索包含菜单关键字的行
    keywords = ['logout', 'signout', 'sign-out', 'userName', 'userInfo', 'nickname']
    
    print("找到的菜单相关内容:")
    print("-" * 100)
    for i, line in enumerate(lines):
        for keyword in keywords:
            if keyword.lower() in line.lower():
                print(f"第 {i+1} 行: {line[:200]}")
                # 显示上下文
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    print(f"   [{j+1}] {lines[j][:100]}")
                print()
                break

if __name__ == '__main__':
    find_menu_items()