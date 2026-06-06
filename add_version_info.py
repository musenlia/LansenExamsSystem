#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def add_version_info_to_js():
    """向前端JavaScript文件添加版本信息获取和管理中心链接显示逻辑"""
    
    js_path = r'E:\ExamsSystem_2.0\app\static\assets\index-BBOw3PVB.js'
    
    # 读取原文件
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加版本信息获取逻辑到文件末尾
    version_code = '''

// 添加版本信息和管理中心链接逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 获取版本信息
    fetch('/api/system/about')
        .then(response => response.json())
        .then(data => {
            if (data.code === 0 && data.data) {
                // 创建版本信息元素
                const versionBadge = document.createElement('div');
                versionBadge.className = 'version-badge';
                versionBadge.textContent = data.data.version;
                versionBadge.style.cssText = `
                    position: fixed;
                    top: 20px;
                    left: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 500;
                    z-index: 9999;
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
                `;
                document.body.appendChild(versionBadge);
            }
        })
        .catch(err => console.log('获取版本信息失败:', err));

    // 显示管理中心链接（管理员登录后显示）
    const adminLink = document.getElementById('admin-link');
    if (adminLink) {
        // 检查是否有token，有则显示管理链接
        const token = localStorage.getItem('access_token');
        if (token) {
            adminLink.classList.add('show');
        }
        
        // 登录成功后显示管理链接
        const observer = new MutationObserver(() => {
            const newToken = localStorage.getItem('access_token');
            if (newToken && adminLink) {
                adminLink.classList.add('show');
            }
        });
        observer.observe(document.documentElement, { childList: true, subtree: true });
    }
});
'''
    
    # 添加代码到文件末尾
    content += version_code
    
    # 写回文件
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已成功添加版本信息和管理中心链接逻辑")

if __name__ == '__main__':
    add_version_info_to_js()