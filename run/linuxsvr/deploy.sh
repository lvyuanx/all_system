#!/usr/bin/env bash
# 一键构建 + 部署 + 刷新 nginx
# 用法：
#   bash deploy.sh -s dev -p all_system -d lvyx.cc
#   bash deploy.sh          # 交互式提示输入
#   bash deploy.sh ... --no-cache --no-nginx

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------- 解析命令行参数 ----------
SITE=""
PROJECT=""
DOMAIN=""
HTTPS="true"
LISTEN="80"
NGINX_RELOAD_DIR="/home/applications/ng_container"
HOST_DATA=""
NO_CACHE=""
NO_NGINX=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--site)       SITE="$2";             shift 2 ;;
        -p|--project)    PROJECT="$2";           shift 2 ;;
        -d|--domain)     DOMAIN="$2";            shift 2 ;;
        --https)         HTTPS="true";           shift ;;
        --no-https)      HTTPS="false";          shift ;;
        --listen)        LISTEN="$2";            shift 2 ;;
        --nginx-dir)     NGINX_RELOAD_DIR="$2";  shift 2 ;;
        --host-data)     HOST_DATA="$2";         shift 2 ;;
        --no-cache)      NO_CACHE="--no-cache";  shift ;;
        --no-nginx)      NO_NGINX=1;             shift ;;
        *) echo "未知参数: $1" >&2; exit 1 ;;
    esac
done

# ---------- 交互式补全缺少的必填项 ----------
prompt() {
    local var_name="$1" prompt_text="$2" default="${3:-}"
    local value
    if [ -n "$default" ]; then
        read -r -p "$prompt_text [$default]: " value
        echo "${value:-$default}"
    else
        while true; do
            read -r -p "$prompt_text: " value
            [ -n "$value" ] && break
            echo "  不能为空，请重新输入" >&2
        done
        echo "$value"
    fi
}

[ -z "$SITE" ]    && SITE=$(prompt SITE    "站点标识 (site, 如 dev/prod)")
[ -z "$PROJECT" ] && PROJECT=$(prompt PROJECT "项目名 (project)" "all_system")
[ -z "$DOMAIN" ]  && DOMAIN=$(prompt DOMAIN  "根域名 (domain, 如 lvyx.cc，留空跳过)" "__skip__")
[ "$DOMAIN" = "__skip__" ] && DOMAIN=""

[ -z "$HOST_DATA" ] && HOST_DATA="/data/$PROJECT"

echo ""
echo "========================================"
echo " site=$SITE  project=$PROJECT  domain=${DOMAIN:-<无>}"
echo "========================================"

CONTAINER_NAME="${PROJECT}_${SITE}"
DEPLOY_CONFIG="$HOST_DATA/$SITE/config.py"

# ---------- 1) 构建镜像 ----------
echo ""
echo "[1/5] 构建镜像..."
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

# ---------- 2) 初始化部署（加载镜像 + 启动容器）----------
echo ""
echo "[2/5] 初始化部署..."
python3 "$LATEST_DIR/init.py"

# ---------- 3) 更新 config.py ----------
echo ""
echo "[3/5] 更新 config.py..."

if [ ! -f "$DEPLOY_CONFIG" ]; then
    echo "未找到 $DEPLOY_CONFIG，跳过 config.py 更新" >&2
else
    if [ -n "$DOMAIN" ]; then
        SLUG=$(echo "${SITE}-${PROJECT}" | tr '_' '-')
        SERVER_NAME="${SLUG}.${DOMAIN}"
    else
        SERVER_NAME="localhost"
    fi

    if [ "$HTTPS" = "true" ]; then
        CSRF_ORIGIN="https://$SERVER_NAME"
    else
        CSRF_ORIGIN="http://$SERVER_NAME"
    fi

    python3 - "$DEPLOY_CONFIG" "$SERVER_NAME" "$CSRF_ORIGIN" "$PROJECT" "$SITE" <<'PYEOF'
import sys, re

config_path, server_name, csrf_origin, project, site = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
text = open(config_path, encoding="utf-8").read()

db_name_raw   = "{}_{}".format(project, site)
allowed_val   = '["{}","localhost","127.0.0.1"]'.format(server_name)
csrf_val      = '["{}"]'.format(csrf_origin)
db_name_val   = '"{}"'.format(db_name_raw)
redis_pfx_val = '"{}"'.format(db_name_raw)

def set_var(src, name, value):
    import re
    pattern = r'^' + name + r'\s*=.*$'
    new_line = '{}={}'.format(name, value)
    if re.search(pattern, src, re.MULTILINE):
        return re.sub(pattern, new_line, src, flags=re.MULTILINE)
    return src.rstrip('\n') + '\n' + new_line + '\n'

text = set_var(text, 'ALLOWED_HOSTS', allowed_val)
text = set_var(text, 'CSRF_TRUSTED_ORIGINS', csrf_val)
text = set_var(text, 'DB_NAME', db_name_val)
text = set_var(text, 'REDIS_KEY_PREFIX', redis_pfx_val)
open(config_path, 'w', encoding='utf-8').write(text)
print("  ALLOWED_HOSTS={}".format(allowed_val))
print("  CSRF_TRUSTED_ORIGINS={}".format(csrf_val))
print("  DB_NAME={}".format(db_name_val))
print("  REDIS_KEY_PREFIX={}".format(redis_pfx_val))
PYEOF
fi

# ---------- 4) 创建数据库 + migrate + init + superuser ----------
echo ""
echo "[4/5] 数据库确认 + migrate..."

DB_NAME="${PROJECT}_${SITE}"

DB_SQL="CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
echo ""
echo "  请手动确认数据库已存在，或执行以下语句创建："
echo ""
echo "    ${DB_SQL}"
echo ""
read -r -p "  数据库 \`${DB_NAME}\` 已就绪？继续部署请按 Enter，中止请按 Ctrl+C ..."

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

echo "  执行自定义初始化命令..."
docker exec "$CONTAINER_NAME" python manage.py init

echo "  创建超级用户 admin..."
docker exec \
    -e DJANGO_SUPERUSER_USERNAME=admin \
    -e DJANGO_SUPERUSER_PASSWORD=123456 \
    -e DJANGO_SUPERUSER_EMAIL=admin@admin.com \
    "$CONTAINER_NAME" \
    python manage.py createsuperuser --noinput 2>&1 | grep -v "already exists" || true

# ---------- 5) 生成 nginx 配置 + reload ----------
echo ""
echo "[5/5] 生成 nginx 配置..."
NGINX_ARGS=("--listen" "$LISTEN")
[ "$HTTPS" = "true" ] && NGINX_ARGS+=("--https") || NGINX_ARGS+=("--no-https")
python3 "$LATEST_DIR/register_nginx.py" "${NGINX_ARGS[@]}"

if [ "$NO_NGINX" -eq 0 ]; then
    if [ -f "$NGINX_RELOAD_DIR/reload.sh" ]; then
        echo "重载 nginx..."
        bash "$NGINX_RELOAD_DIR/reload.sh"
    else
        echo "未找到 $NGINX_RELOAD_DIR/reload.sh，跳过 nginx 重载" >&2
    fi
else
    echo "跳过 nginx 重载（--no-nginx）"
fi

# ---------- 保存配置供 update.sh 使用 ----------
SAVED_CONFIG="$HOST_DATA/$SITE/build.json"
python3 - "$SAVED_CONFIG" "$SITE" "$PROJECT" "$DOMAIN" "$HTTPS" "$LISTEN" "$NGINX_RELOAD_DIR" "$HOST_DATA" <<'PYEOF'
import sys, json
path, site, project, domain, https, listen, nginx_dir, host_data = sys.argv[1:]
data = {
    "site": site,
    "project": project,
    "domain": domain,
    "https": https == "true",
    "listen": int(listen),
    "nginx_reload_dir": nginx_dir,
    "host_data": host_data,
}
json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print("  配置已保存至: {}".format(path))
PYEOF

echo ""
echo "======== 部署完成 ========"
