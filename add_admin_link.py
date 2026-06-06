#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def add_admin_center_link():
    """在左侧菜单栏中添加管理中心链接"""
    
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    # 读取原文件
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加过管理中心链接
    if '管理中心' in content and 'key:"admin"' in content:
        print("管理中心链接已存在，无需重复添加")
        return
    
    # 查找菜单配置位置 - 在"参数配置"后面添加管理中心
    # 找到菜单配置的模式
    old_pattern = 'key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]})'
    new_pattern = 'key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]})},{key:"admin",label:T.jsxs("span",{children:[T.jsx(bee,{})," 管理中心"]}),onClick:function(){window.open("/admin.html","_blank")}'
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        # 写回文件
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("已成功在左侧菜单栏添加管理中心链接")
    else:
        print("未找到菜单配置位置")

if __name__ == '__main__':
    add_admin_center_link()