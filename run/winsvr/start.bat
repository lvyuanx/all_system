@echo off
chcp 65001 >nul

REM ===============================================
REM 启动 Django uvserver (Windows)
REM Author: lyx
REM ===============================================

REM 获取当前 bat 文件所在目录（带反斜杠结尾）
SET "SCRIPT_DIR=%~dp0"

REM 获取项目根目录（假设 manage.py 在 bat 的上上级）
FOR %%I IN ("%SCRIPT_DIR%..\..\") DO SET "PROJECT_DIR=%%~fI"

REM 设置 manage.py 绝对路径
SET "MANAGE_PATH=%PROJECT_DIR%\manage.py"

echo [1/2] 激活虚拟环境 ...
call "%SCRIPT_DIR%venv\Scripts\activate"

if not exist "%MANAGE_PATH%" (
    echo ❌ 未找到 manage.py ：%MANAGE_PATH%
    pause
    exit /b 1
)

echo [2/2] 启动 Django uvserver ...
python "%MANAGE_PATH%" uvserver --host 0.0.0.0 --port 8080

if %errorlevel% neq 0 (
    echo ❌ 启动失败，错误代码：%errorlevel%
) else (
    echo ✅ 启动成功！
)

echo 程序已关闭...
pause

