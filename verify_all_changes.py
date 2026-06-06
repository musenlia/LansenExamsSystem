#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def verify_all_changes():
    """验证所有修改是否真实存在"""
    
    print("=" * 80)
    print("自我核查：验证所有声称的修改")
    print("=" * 80)
    
    # 1. 检查考试服务中的reactivate方法
    print("\n[1] 检查 app/services/exam_service.py")
    print("-" * 80)
    try:
        with open(r'E:\ExamsSystem_2.0\app\services\exam_service.py', 'r', encoding='utf-8') as f:
            exam_service = f.read()
        
        if 'def reactivate(' in exam_service:
            print("OK: reactivate 方法存在于 exam_service.py")
            # 提取方法片段
            start = exam_service.find('def reactivate(')
            end = exam_service.find('\n    @staticmethod', start + 1)
            if end == -1:
                end = exam_service.find('\n\n', start)
            print("方法片段：")
            print(exam_service[start:end if end != -1 else start + 500])
        else:
            print("FAIL: reactivate 方法不存在于 exam_service.py")
    except Exception as e:
        print(f"ERROR: 读取文件失败 - {e}")
    
    # 2. 检查考试路由中的reactivate API
    print("\n[2] 检查 app/routers/exam.py")
    print("-" * 80)
    try:
        with open(r'E:\ExamsSystem_2.0\app\routers\exam.py', 'r', encoding='utf-8') as f:
            exam_router = f.read()
        
        if '/reactivate' in exam_router:
            print("OK: /reactivate 路由存在于 exam.py")
            # 提取路由片段
            start = exam_router.find('def reactivate_exam')
            end = exam_router.find('\n\n', start)
            if end == -1:
                end = start + 500
            print("路由片段：")
            print(exam_router[start:end if end != -1 else start + 500])
        else:
            print("FAIL: /reactivate 路由不存在于 exam.py")
    except Exception as e:
        print(f"ERROR: 读取文件失败 - {e}")
    
    # 3. 检查管理页面中的重新激活按钮和函数
    print("\n[3] 检查 app/static/admin.html")
    print("-" * 80)
    try:
        with open(r'E:\ExamsSystem_2.0\app\static\admin.html', 'r', encoding='utf-8') as f:
            admin_html = f.read()
        
        if '重新激活考试' in admin_html:
            print("OK: 重新激活考试按钮存在于 admin.html")
        else:
            print("FAIL: 重新激活考试按钮不存在于 admin.html")
        
        if 'btnReactivate' in admin_html:
            print("OK: btnReactivate 元素存在于 admin.html")
        else:
            print("FAIL: btnReactivate 元素不存在于 admin.html")
        
        if 'async function reactivateExam()' in admin_html or 'function reactivateExam()' in admin_html:
            print("OK: reactivateExam 函数存在于 admin.html")
        else:
            print("FAIL: reactivateExam 函数不存在于 admin.html")
            
    except Exception as e:
        print(f"ERROR: 读取文件失败 - {e}")
    
    # 4. 检查前端JS中的管理中心链接
    print("\n[4] 检查 app/static/assets/index-BBOw3PVB.js")
    print("-" * 80)
    try:
        with open(r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        if '管理中心' in js_content:
            print("OK: 管理中心文字存在于 JS 文件")
        else:
            print("FAIL: 管理中心文字不存在于 JS 文件")
        
        if 'admin.html' in js_content:
            print("OK: admin.html 链接存在于 JS 文件")
        else:
            print("FAIL: admin.html 链接不存在于 JS 文件")
            
        if 'key:"admin"' in js_content:
            print("OK: admin 菜单键存在")
        else:
            print("FAIL: admin 菜单键不存在")
            
    except Exception as e:
        print(f"ERROR: 读取文件失败 - {e}")
    
    # 5. 检查服务是否在运行
    print("\n[5] 检查服务状态")
    print("-" * 80)
    import subprocess
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        if ':8000' in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if ':8000' in line and 'LISTENING' in line:
                    print(f"OK: 服务正在运行 - {line.strip()}")
                    break
        else:
            print("FAIL: 服务未在8000端口运行")
    except Exception as e:
        print(f"ERROR: 检查服务状态失败 - {e}")
    
    print("\n" + "=" * 80)
    print("核查完成")
    print("=" * 80)

if __name__ == '__main__':
    verify_all_changes()