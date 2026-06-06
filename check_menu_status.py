#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def check_menu_status():
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    admin_path = r'E:\ExamsSystem_2.0\app\static\admin.html'
    
    print("=== 检查左侧菜单 ===")
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    if '管理中心' in js_content:
        print("OK: 管理中心链接已存在于左侧菜单")
    else:
        print("NO: 管理中心链接不存在于左侧菜单")
    
    if 'admin.html' in js_content:
        print("OK: admin.html 链接已存在")
    else:
        print("NO: admin.html 链接不存在")
    
    print("\n=== 检查管理页面 ===")
    with open(admin_path, 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    if '重新激活考试' in admin_content:
        print("OK: 重新激活考试按钮已存在")
    else:
        print("NO: 重新激活考试按钮不存在")
    
    if 'btnReactivate' in admin_content:
        print("OK: 重新激活按钮元素已定义")
    else:
        print("NO: 重新激活按钮元素未定义")

if __name__ == '__main__':
    check_menu_status()