#!/bin/bash
# ===============================================
# 初始化 Python 虚拟环境并安装依赖 (Linux/macOS)
# Author: lyx
# ===============================================

set -e

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 项目根目录（假设 requirements 在脚本目录的上上级）
REQ_BASE="$SCRIPT_DIR/../../"

echo "[1/5] 创建虚拟环境 venv ..."
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    python3 -m venv "$SCRIPT_DIR/venv"
else
    echo "虚拟环境已存在，跳过创建。"
fi

echo "[2/5] 激活虚拟环境 ..."
source "$SCRIPT_DIR/venv/bin/activate"

echo "[3/5] 升级 pip ..."
pip install --upgrade pip

echo "[4/5] 安装依赖 ..."
if [ -f "${REQ_BASE}requirements.txt" ]; then
    echo "-> 安装 ${REQ_BASE}requirements.txt ..."
    pip install -r "${REQ_BASE}requirements.txt"
else
    echo "⚠️ 未找到 ${REQ_BASE}requirements.txt"
fi

if [ -f "${REQ_BASE}requirements_linux.txt" ]; then
    echo "-> 安装 ${REQ_BASE}requirements_linux.txt ..."
    pip install -r "${REQ_BASE}requirements_linux.txt"
else
    echo "⚠️ 未找到 ${REQ_BASE}requirements_linux.txt"
fi

echo "[5/5] 初始化环境 ..."
echo "-> 初始化 Playwright 运行环境 ..."
python -m playwright install chromium
echo "-> 初始化系统 ..."
python "${REQ_BASE}manage.py" init_sys

echo
echo "✅ 初始化完成！"
echo "虚拟环境路径: $SCRIPT_DIR/venv"
echo "运行项目前请执行:"
echo "    source $SCRIPT_DIR/venv/bin/activate"
echo
