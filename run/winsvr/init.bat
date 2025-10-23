@echo off
chcp 65001 >nul

REM ===============================================
REM 初始化 Python 虚拟环境并安装依赖 (Windows)
REM Author: lyx
REM ===============================================

REM 获取当前 bat 文件所在目录
SET "SCRIPT_DIR=%~dp0"

REM 项目根目录（假设 requirements 在 bat 所在目录的上上级）
SET "REQ_BASE=%SCRIPT_DIR%..\..\"

echo [1/5] 创建虚拟环境 venv ...
if not exist "%SCRIPT_DIR%venv" (
    python -m venv "%SCRIPT_DIR%venv"
) else (
    echo 虚拟环境已存在，跳过创建。
)

echo [2/5] 激活虚拟环境 ...
call "%SCRIPT_DIR%venv\Scripts\activate"

echo [3/5] 升级 pip ...
pip install --upgrade pip

echo [4/5] 安装依赖 ...
if exist "%REQ_BASE%requirements.txt" (
    echo  安装 %REQ_BASE%requirements.txt ...
    pip install -r "%REQ_BASE%requirements.txt"
) else (
    echo ⚠️ 未找到 %REQ_BASE%requirements.txt
)

if exist "%REQ_BASE%requirements_win.txt" (
    echo  安装 %REQ_BASE%requirements_win.txt ...
    pip install -r "%REQ_BASE%requirements_win.txt"
) else (
    echo ⚠️ 未找到 %REQ_BASE%requirements_win.txt
)

echo [5/5] 初始化环境 ...
echo 初始化 Playwright 运行环境 ..
python -m playwright install chromium
echo 初始化系统 ..
python "%REQ_BASE%manage.py" init_sys

echo.
echo ✅ 初始化完成！
echo 虚拟环境路径: %SCRIPT_DIR%venv
echo 运行项目前请执行:
echo     call "%SCRIPT_DIR%venv\Scripts\activate"
echo.
pause
