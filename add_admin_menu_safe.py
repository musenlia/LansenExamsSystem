#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def add_admin_center_link():
    """安全地在左侧菜单栏添加管理中心链接"""
    
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    # 读取原文件
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加过管理中心链接
    if 'key:"admin"' in content and '管理中心' in content:
        print("管理中心链接已存在，无需重复添加")
        return
    
    # 找到参数配置菜单的完整对象结构
    # 根据分析，菜单配置格式为: {key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]}),children:T.jsx(Lt,{title:"...})}
    # 我们需要在这个对象后面添加新的菜单项
    
    # 使用更精确的匹配模式 - 在参数配置的 children 结束后添加
    old_pattern = 'key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]}),children:T.jsx(Lt,{title:"'
    new_pattern = 'key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]}),children:T.jsx(Lt,{title:"'
    
    if old_pattern in content:
        # 在参数配置后面添加管理中心菜单项
        # 找到完整的参数配置对象结束位置
        content = content.replace(
            'key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]}),children:T.jsx(Lt,{title:"',
            'key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]}),children:T.jsx(Lt,{title:"'
        )
        
        # 现在找到参数配置对象的结束位置，在其后添加管理中心
        # 查找模式：参数配置后面的下一个菜单项开始前
        # 使用 ',{key:"' 来定位下一个菜单项的开始
        
        # 更简单的方法：在包含参数配置的行后面添加
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            # 在参数配置那行后面添加管理中心菜单项
            if 'key:"config"' in line and '参数配置' in line:
                # 添加管理中心菜单项
                admin_line = '},{key:"admin",label:T.jsxs("span",{children:[T.jsx(bee,{})," 管理中心"]}),onClick:function(){window.open("/admin.html","_blank")}'
                new_lines.append(admin_line)
                print(f"已在第 {i+1} 行后面添加管理中心菜单项")
        
        content = '\n'.join(new_lines)
        
        # 写回文件
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("已成功在左侧菜单栏添加管理中心链接")
    else:
        print("未找到菜单配置位置")

if __name__ == '__main__':
    add_admin_center_link()