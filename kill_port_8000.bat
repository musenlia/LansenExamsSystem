@echo off
chcp 65001 >nul

echo ============================================================
echo   Kill Process Using Port 8000
echo ============================================================

:: 查找占用 8000 端口的 PID
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000') do (
    echo 发现占用端口的 PID：%%i
    taskkill /PID %%i /F >nul 2>&1
    if not errorlevel 1 (
        echo 已成功结束 PID：%%i
    ) else (
        echo 结束 PID：%%i 失败，请确认是否以管理员身份运行
    )
)

echo.
echo ============================================================
echo   当前 8000 端口占用情况
echo ============================================================
netstat -ano | findstr :8000

echo.
pause