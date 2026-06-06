def fix_admin_menu():
    with open(r'e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 先删除之前错误插入的管理中心链接
    old_admin_link = ',{key:"admin",label:T.jsxs("span",{children:[T.jsx(bee,{})," 管理中心"]}),onClick:function(){window.open("/admin.html","_blank")}}'
    if old_admin_link in content:
        content = content.replace(old_admin_link, '}}')
        print("✓ 删除了错误位置的管理中心链接")
    
    # 2. 在系统设置后面添加管理中心链接
    search_str = '{key:"/admin/settings",icon:T.jsx(bee,{}),label:"系统设置",roles:["admin"]}'
    replace_str = search_str + ',{key:"admin_center",label:"管理中心",icon:T.jsx(bee,{}),roles:["admin"],onClick:function(){window.open("/admin.html","_blank")}}'
    
    if search_str in content:
        content = content.replace(search_str, replace_str)
        print("✓ 在系统设置后添加了管理中心链接")
    else:
        print("✗ 未找到系统设置菜单项")
    
    with open(r'e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n修复完成！")
    
    # 验证
    with open(r'e:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'admin_center' in content and '管理中心' in content:
        print("✓ 验证成功：管理中心链接已正确添加")
    else:
        print("✗ 验证失败：管理中心链接未正确添加")

if __name__ == "__main__":
    fix_admin_menu()