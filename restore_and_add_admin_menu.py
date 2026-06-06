#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def restore_and_add_admin_menu():
    """从备份恢复并添加管理中心链接"""
    
    # 备份文件路径
    backup_path = r'E:\ExamsSystem_Backup\ExamsSystem_Backup_20260602_154129\app\static\assets\index-BBOw3PVB.js'
    target_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    # 读取备份文件
    with open(backup_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已存在管理中心
    if 'key:"admin"' in content and '管理中心' in content:
        print("管理中心链接已存在，无需添加")
        return
    
    # 找到参数配置的位置并添加管理中心
    # 查找模式：key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]})
    old_pattern = 'key:"config",label:T.jsxs("span",{children:[T.jsx(bee,{})," 参数配置"]})'
    
    if old_pattern in content:
        # 在参数配置后面添加管理中心
        # 创建新的菜单项
        admin_menu_item = ',{key:"admin",label:T.jsxs("span",{children:[T.jsx(bee,{})," 管理中心"]}),onClick:function(){window.open("/admin.html","_blank")}}'
        
        # 找到参数配置的完整对象位置
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if old_pattern in line:
                # 在包含参数配置的行后面添加管理中心
                new_lines.append(admin_menu_item)
                print(f"已在第 {i+1} 行添加管理中心菜单项")
        
        content = '\n'.join(new_lines)
        
        # 写回文件
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("成功添加管理中心链接到左侧菜单")
    else:
        print("未找到菜单配置位置")

if __name__ == '__main__':
    restore_and_add_admin_menu()