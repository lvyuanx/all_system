#!/usr/bin/env bash
# 一键构建 + 部署 + 刷新 nginx
# 用法：bash deploy.sh [--no-cache] [--no-nginx]
# 配置从同目录 build.json 读取

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SCRIPT_DIR/build.json"

# ---------- 读取 build.json ----------
if [ ! -f "$CONFIG" ]; then
    echo "未找到配置文件: $CONFIG" >&2
    exit 1
fi

read_json() {
    python3 -c "import json,sys; d=json.load(open('$CONFIG')); print(d.get('$1',''))"
}

SITE=$(read_json site)
PROJECT=$(read_json project)
DOMAIN=$(read_json domain)
HTTPS=$(read_json https)
LISTEN=$(read_json listen)
NGINX_RELOAD_DIR=$(read_json nginx_reload_dir)

# ---------- 解析命令行参数 ----------
NO_CACHE=""
NO_NGINX=0
for arg in "$@"; do
    case "$arg" in
        --no-cache) NO_CACHE="--no-cache" ;;
        --no-nginx) NO_NGINX=1 ;;
    esac
done

echo "========================================"
echo " site=$SITE  project=$PROJECT  domain=$DOMAIN"
echo "========================================"

# ---------- 1) 构建镜像 ----------
echo ""
echo "[1/3] 构建镜像..."
BUILD_ARGS=(-s "$SITE" -p "$PROJECT")
[ -n "$DOMAIN" ] && BUILD_ARGS+=(-d "$DOMAIN")
[ -n "$NO_CACHE" ] && BUILD_ARGS+=("$NO_CACHE")

python3 "$SCRIPT_DIR/build_image.py" "${BUILD_ARGS[@]}"

# ---------- 找到最新产出目录 ----------
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"
LATEST_DIR=$(ls -td "$BUILD_DIR"/[0-9]* 2>/dev/null | head -1)

if [ -z "$LATEST_DIR" ]; then
    echo "未找到构建产物目录: $BUILD_DIR" >&2
    exit 1
fi

echo "产物目录: $LATEST_DIR"

# ---------- 2) 初始化部署 ----------
echo ""
echo "[2/3] 初始化部署..."
python3 "$LATEST_DIR/init.py"

# ---------- 2b) 写入 ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS ----------
echo ""
echo "[2b/3] 更新 config.py 中的 ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS / DB_NAME / REDIS_KEY_PREFIX..."

HOST_DATA=$(read_json host_data)
if [ -z "$HOST_DATA" ]; then
    HOST_DATA="/data/$PROJECT"
fi
DEPLOY_CONFIG="$HOST_DATA/$SITE/config.py"

if [ ! -f "$DEPLOY_CONFIG" ]; then
    echo "未找到 $DEPLOY_CONFIG，跳过 ALLOWED_HOSTS 配置" >&2
else
    # 构建 server_name：与 build_image.py 保持一致
    if [ -n "$DOMAIN" ]; then
        SLUG=$(echo "${SITE}-${PROJECT}" | tr '_' '-')
        SERVER_NAME="${SLUG}.${DOMAIN}"
    else
        SERVER_NAME="localhost"
    fi

    # HTTPS 时同时信任 https://  协议头
    if [ "$HTTPS" = "True" ]; then
        CSRF_ORIGIN="https://$SERVER_NAME"
    else
        CSRF_ORIGIN="http://$SERVER_NAME"
    fi

    # 用 python3 原地更新或追加，避免重复写入
    python3 - "$DEPLOY_CONFIG" "$SERVER_NAME" "$CSRF_ORIGIN" "$PROJECT" "$SITE" <<'PYEOF'
import sys, re

config_path, server_name, csrf_origin, project, site = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
text = open(config_path, encoding="utf-8").read()

db_name_raw   = f"{project}_{site}"
allowed_val   = f'["{server_name}", "localhost", "127.0.0.1"]'
csrf_val      = f'["{csrf_origin}"]'
db_name_val   = f'"{db_name_raw}"'
redis_pfx_val = f'"{db_name_raw}"'

def set_var(src, name, value):
    pattern = rf'^{name}\s*=.*$'
    new_line = f'{name}={value}'
    if re.search(pattern, src, re.MULTILINE):
        return re.sub(pattern, new_line, src, flags=re.MULTILINE)
    return src.rstrip('\n') + f'\n{new_line}\n'

text = set_var(text, 'ALLOWED_HOSTS', allowed_val)
text = set_var(text, 'CSRF_TRUSTED_ORIGINS', csrf_val)
text = set_var(text, 'DB_NAME', db_name_val)
text = set_var(text, 'REDIS_KEY_PREFIX', redis_pfx_val)
open(config_path, 'w', encoding='utf-8').write(text)
print(f"  ALLOWED_HOSTS={allowed_val}")
print(f"  CSRF_TRUSTED_ORIGINS={csrf_val}")
print(f"  DB_NAME={db_name_val}")
print(f"  REDIS_KEY_PREFIX={redis_pfx_val}")
PYEOF
fi

# ---------- 2c) 创建数据库 + migrate ----------
echo ""
echo "[2c/3] 创建数据库并执行 migrate..."

DB_NAME="${PROJECT}_${SITE}"
CONTAINER_NAME="${PROJECT}_${SITE}"

# 从部署 config.py 读取 DB 连接信息
python3 - "$DEPLOY_CONFIG" "$DB_NAME" <<'PYEOF'
import sys, re, subprocess

config_path, db_name = sys.argv[1], sys.argv[2]
text = open(config_path, encoding="utf-8").read()

def get_var(src, name, default=""):
    m = re.search(rf'^{name}\s*=\s*["\']?(.*?)["\']?\s*$', src, re.MULTILINE)
    return m.group(1).strip() if m else default

host     = get_var(text, "DB_HOST", "127.0.0.1")
port     = get_var(text, "DB_PORT", "3306")
user     = get_var(text, "DB_USER", "root")
password = get_var(text, "DB_PASSWORD", "")

sql = f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
cmd = ["mysql", f"-h{host}", f"-P{port}", f"-u{user}", f"-p{password}", "-e", sql]
print(f"$ mysql -h{host} -P{port} -u{user} -p*** -e \"{sql}\"")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)
print(f"  数据库 `{db_name}` 已就绪")
PYEOF

# 等待容器就绪后执行 migrate
echo "  等待容器启动..."
for i in $(seq 1 15); do
    if docker exec "$CONTAINER_NAME" python manage.py check --database default > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo "  执行 makemigrations..."
docker exec "$CONTAINER_NAME" python manage.py makemigrations

echo "  执行 migrate..."
docker exec "$CONTAINER_NAME" python manage.py migrate

# ---------- 2d) 生成 nginx 配置 ----------
echo ""
echo "[2d/3] 生成 nginx 配置..."
NGINX_ARGS=("--listen" "$LISTEN")
[ "$HTTPS" = "True" ] && NGINX_ARGS+=("--https") || NGINX_ARGS+=("--no-https")

python3 "$LATEST_DIR/register_nginx.py" "${NGINX_ARGS[@]}"

# ---------- 3) 重载 nginx ----------
if [ "$NO_NGINX" -eq 0 ]; then
    echo ""
    echo "[3/3] 重载 nginx..."
    if [ -f "$NGINX_RELOAD_DIR/reload.sh" ]; then
        bash "$NGINX_RELOAD_DIR/reload.sh"
    else
        echo "未找到 $NGINX_RELOAD_DIR/reload.sh，跳过 nginx 重载" >&2
    fi
else
    echo "[3/3] 跳过 nginx 重载（--no-nginx）"
fi

echo ""
echo "======== 部署完成 ========"
