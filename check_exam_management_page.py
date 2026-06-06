#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def check_exam_management_page():
    """检查考试管理页面中的操作选项"""
    
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    print("=== 检查考试管理页面中的操作选项 ===")
    print()
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 搜索考试管理相关的操作
    operations = ['发布', '终止', '暂停', '恢复', '归档', '重新激活', 'reactivate']
    
    print("已找到的考试操作：")
    for op in operations:
        if op in content:
            print(f"  ✓ {op}")
        else:
            print(f"  ✗ {op}")
    
    print("\n=== 分析结果 ===")
    if '重新激活' in content or 'reactivate' in content:
        print("重新激活功能已存在于前端代码中")
    else:
        print("重新激活功能可能只在管理中心页面，不在主考试管理页面")
    
    # 检查是否有调用reactivate API的代码
    if '/api/exams/' in content and 'reactivate' in content:
        print("前端代码中存在调用重新激活API的逻辑")
    else:
        print("前端代码中未发现调用重新激活API的逻辑")

if __name__ == '__main__':
    check_exam_management_page()