@echo off
chcp 65001 >nul
title 关闭考试系统服务器

echo ============================================
echo   学习培训考试管理系统 - 停止服务
echo ============================================
echo.

:: 1. 杀掉 uvicorn 进程 (端口 8000)
echo [1/3] 正在停止 Web 服务器 (端口 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo   已终止进程 PID: %%a
)

:: 2. 杀掉所有 Python 进程 (备用)
echo [2/3] 正在检查残留 Python 进程...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr "python.exe" >nul
if %errorlevel% equ 0 (
    taskkill /F /IM python.exe >nul 2>&1
    echo   已终止所有 Python 进程
) else (
    echo   没有残留 Python 进程
)

:: 3. 确认端口释放
echo [3/3] 验证端口 8000 已释放...
netstat -ano | findstr ":8000.*LISTENING" >nul
if %errorlevel% neq 0 (
    echo   端口 8000 已释放
) else (
    echo   警告: 端口 8000 可能仍被占用
)

echo.
echo ============================================
echo   考试系统已完全停止
echo ============================================
pause
