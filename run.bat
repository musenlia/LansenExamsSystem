@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Learning Exam Training System

:: ============================================================
::  Learning Exam Training System - Portable Edition
::  One-click startup - no installation required
:: ============================================================

set "ROOT_DIR=%~dp0"
set "APP_DIR=%ROOT_DIR%app"
set "VENV_DIR=%ROOT_DIR%venv"
set "DATA_DIR=%ROOT_DIR%data"
set "PYTHON=%ROOT_DIR%python\python.exe"
set "SERVE_PORT=8000"
set "LOCAL_IP="

echo ============================================================
echo   Learning Exam Training System - Portable Edition
echo ============================================================
echo.

:: ============================================================
:: Get local IP address
:: ============================================================
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4 Address" ^| findstr /v "127.0.0.1" ^| findstr /v "169.254"') do (
    set "LOCAL_IP=%%a"
    set "LOCAL_IP=!LOCAL_IP: =!"
    goto :IP_FOUND
)
:IP_FOUND
if not defined LOCAL_IP set "LOCAL_IP=127.0.0.1"

:: ============================================================
:: Step 1: Auto-initialize database on first run
:: ============================================================
if not exist "%DATA_DIR%\exam_system.db" (
    echo [1/3] First run detected - initializing database...
    "%PYTHON%" "%APP_DIR%\init_data.py"
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Database initialization failed.
        pause
        exit /b 1
    )
    echo [OK] Database initialized.
) else (
    echo [1/3] Database found.
)
echo.

:: ============================================================
:: Step 2: Start server
:: ============================================================
echo [2/3] Starting server on port %SERVE_PORT%...
cd /d "%APP_DIR%"

:: Open browser with IP address
start "" "http://%LOCAL_IP%:%SERVE_PORT%"

echo.
echo ============================================================
echo   System is starting up...
echo   Local IP: %LOCAL_IP%
echo   Access: http://%LOCAL_IP%:%SERVE_PORT%
echo   Default admin: admin / admin123
echo   Press Ctrl+C to stop the server
echo ============================================================
echo.
echo [3/3] Server is running - below is the Python output:
echo.

"%PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port %SERVE_PORT%

:: ============================================================
:: After server stops
:: ============================================================
echo.
echo ============================================================
echo   Service stopped.
echo   Close this window or press any key to exit.
echo ============================================================
echo.
pause
