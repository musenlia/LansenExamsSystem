#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def find_menu_items():
    """查找菜单相关内容"""
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 搜索包含菜单关键字的行
    keywords = ['退出登录', '退出', '登录', '用户', '个人', '设置', '系统', '关于']
    
    print("找到的菜单相关内容:")
    print("-" * 100)
    for i, line in enumerate(lines):
        for keyword in keywords:
            if keyword in line and len(line) < 200:
                print(f"第 {i+1} 行: {line}")
                break

if __name__ == '__main__':
    find_menu_items()