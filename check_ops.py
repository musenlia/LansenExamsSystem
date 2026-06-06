#!/usr/bin/env python3

def check_ops():
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    ops = ['发布', '终止', '暂停', '恢复', '归档', '重新激活']
    
    print("Exam Management Operations Check:")
    for op in ops:
        if op in content:
            print(f"Found: {op}")
        else:
            print(f"Not found: {op}")
    
    print("\nAdmin page check:")
    admin_path = r'E:\ExamsSystem_2.0\app\static\admin.html'
    with open(admin_path, 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    if '重新激活考试' in admin_content:
        print("Reactivate button in admin.html: YES")
    else:
        print("Reactivate button in admin.html: NO")

if __name__ == '__main__':
    check_ops()