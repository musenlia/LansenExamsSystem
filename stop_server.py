# -*- coding: utf-8 -*-
"""
考试系统 - 一键停止所有服务
双击运行或命令行: python stop_server.py
"""
import os
import sys
import subprocess
import time


def find_processes_by_port(port=8000):
    """查找占用指定端口的进程 PID 列表"""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True, text=True, encoding='gbk', errors='replace'
        )
        pids = set()
        for line in result.stdout.split('\n'):
            # 匹配 ":端口号 " 并且有 LISTENING
            if f':{port} ' in line and 'LISTENING' in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid.isdigit() and pid != '0':
                    pids.add(pid)
        return pids
    except Exception as e:
        print(f"  查找进程失败: {e}")
        return set()


def kill_process(pid):
    """强制终止指定 PID 的进程"""
    try:
        subprocess.run(
            ['taskkill', '/F', '/PID', str(pid)],
            capture_output=True, check=False
        )
        return True
    except Exception as e:
        print(f"  终止 PID {pid} 失败: {e}")
        return False


def main():
    print("=" * 50)
    print("  学习培训考试管理系统 - 停止服务")
    print("=" * 50)
    print()

    # 1. 终止端口 8000 的进程
    print("[1/2] 正在停止 Web 服务器 (端口 8000)...")
    pids = find_processes_by_port(8000)
    if pids:
        for pid in pids:
            if kill_process(pid):
                print(f"  ✓ 已终止进程 PID: {pid}")
    else:
        print("  端口 8000 没有监听进程")

    time.sleep(1)

    # 2. 终止所有 Python 进程（清理残留）
    print("[2/2] 正在清理残留 Python 进程...")
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
            capture_output=True, text=True, encoding='gbk', errors='replace'
        )
        if 'python.exe' in result.stdout:
            subprocess.run(
                ['taskkill', '/F', '/IM', 'python.exe'],
                capture_output=True, check=False
            )
            print("  ✓ 已终止所有 Python 进程")
        else:
            print("  没有残留 Python 进程")
    except Exception as e:
        print(f"  清理失败: {e}")

    # 3. 确认
    time.sleep(1)
    remaining = find_processes_by_port(8000)
    print()
    if not remaining:
        print("=" * 50)
        print("  ✓ 考试系统已完全停止")
        print("=" * 50)
    else:
        print("=" * 50)
        print(f"  ⚠ 警告: 端口 8000 仍被进程 {remaining} 占用")
        print("=" * 50)
    print()


if __name__ == "__main__":
    main()
    print("按 Enter 键退出...", end='', flush=True)
    try:
        input()
    except (EOFError, OSError, KeyboardInterrupt):
        print()
