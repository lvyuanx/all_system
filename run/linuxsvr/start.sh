#!/bin/bash
# ===============================================
# 运行 Django 服务 (Linux/macOS)
# Author: lyx
# ===============================================

set -e

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 获取项目根目录（假设 manage.py 在脚本目录的上上级）
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../" && pwd)"

# manage.py 绝对路径
MANAGE_PATH="$PROJECT_DIR/manage.py"

# 检查 manage.py 是否存在
if [ ! -f "$MANAGE_PATH" ]; then
  echo "❌ 未找到 manage.py: $MANAGE_PATH"
  exit 1
fi

echo "[1/2] 激活虚拟环境 ..."
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
  source "$SCRIPT_DIR/venv/bin/activate"
else
  echo "❌ 未找到虚拟环境: $SCRIPT_DIR/venv/bin/activate"
  exit 1
fi

echo "[2/2] 启动 Django uvserver ..."
python "$MANAGE_PATH" uvserver --host 0.0.0.0 --port 8080

status=$?
if [ $status -ne 0 ]; then
  echo "❌ 启动失败，退出码: $status"
  exit $status
else
  echo "✅ 启动成功！"
fi

echo "程序已关闭 ..."
