#!/usr/bin/env bash
# 更新已有容器：构建新镜像 → 替换容器 → migrate
# 用法：
#   bash update.sh -s dev -p all_system       # 手动指定
#   bash update.sh                             # 自动从 /data/<project>/<site>/build.json 读取
#   bash update.sh ... --no-cache --no-nginx

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------- 解析命令行参数 ----------
SITE=""
PROJECT=""
DOMAIN=""
HOST_DATA=""
NGINX_RELOAD_DIR=""
NO_CACHE=""
NO_NGINX=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--site)      SITE="$2";            shift 2 ;;
        -p|--project)   PROJECT="$2";         shift 2 ;;
        -d|--domain)    DOMAIN="$2";          shift 2 ;;
        --host-data)    HOST_DATA="$2";       shift 2 ;;
        --nginx-dir)    NGINX_RELOAD_DIR="$2"; shift 2 ;;
        --no-cache)     NO_CACHE="--no-cache"; shift ;;
        --no-nginx)     NO_NGINX=1;           shift ;;
        *) echo "未知参数: $1" >&2; exit 1 ;;
    esac
done

# ---------- 尝试从已保存的 build.json 读取 ----------
load_saved_config() {
    local saved="$1"
    if [ ! -f "$saved" ]; then
        return 1
    fi
    local val
    val=$(python3 -c "import json; d=json.load(open('$saved')); print(d.get('$2',''))" 2>/dev/null) && echo "$val"
}

# 若 site/project 未从命令行传入，先交互询问以定位 build.json
if [ -z "$SITE" ] || [ -z "$PROJECT" ]; then
    echo "未指定 -s/-p，尝试交互式输入以定位已保存配置..."
    [ -z "$PROJECT" ] && read -r -p "项目名 (project) [all_system]: " PROJECT && PROJECT="${PROJECT:-all_system}"
    [ -z "$SITE" ]    && { read -r -p "站点标识 (site): " SITE; [ -z "$SITE" ] && { echo "site 不能为空" >&2; exit 1; }; }
fi

[ -z "$HOST_DATA" ] && HOST_DATA="/data/$PROJECT"
SAVED_CONFIG="$HOST_DATA/$SITE/build.json"

if [ -f "$SAVED_CONFIG" ]; then
    echo "读取已保存配置: $SAVED_CONFIG"
    read_saved() { python3 -c "import json; d=json.load(open('$SAVED_CONFIG')); print(d.get('$1',''))"; }
    [ -z "$DOMAIN" ]           && DOMAIN=$(read_saved domain)
    [ -z "$NGINX_RELOAD_DIR" ] && NGINX_RELOAD_DIR=$(read_saved nginx_reload_dir)
    HTTPS=$(read_saved https)   # True/False from json bool
else
    echo "未找到已保存配置 $SAVED_CONFIG，使用默认值" >&2
    HTTPS="true"
fi

[ -z "$NGINX_RELOAD_DIR" ] && NGINX_RELOAD_DIR="/home/applications/ng_container"
HTTPS_LOWER=$(echo "$HTTPS" | tr '[:upper:]' '[:lower:]')

CONTAINER_NAME="${PROJECT}_${SITE}"

echo ""
echo "========================================"
echo " 更新: site=$SITE  project=$PROJECT  domain=${DOMAIN:-<无>}"
echo "========================================"

# ---------- 1) 构建新镜像 ----------
echo ""
echo "[1/3] 构建新镜像..."
BUILD_ARGS=(-s "$SITE" -p "$PROJECT")
[ -n "$DOMAIN" ] && BUILD_ARGS+=(-d "$DOMAIN")
[ -n "$NO_CACHE" ] && BUILD_ARGS+=("$NO_CACHE")

python3 "$SCRIPT_DIR/build_image.py" "${BUILD_ARGS[@]}"

# ---------- 找到最新产出目录 ----------
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
# build_image.py ????? /data/build??????? COPY ???
BUILD_DIR="/data/build"
LATEST_DIR=$(ls -td "$BUILD_DIR"/[0-9]* 2>/dev/null | head -1)

if [ -z "$LATEST_DIR" ]; then
    echo "未找到构建产物目录: $BUILD_DIR" >&2
    exit 1
fi
echo "产物目录: $LATEST_DIR"

# ---------- 2) 替换容器 ----------
echo ""
echo "[2/3] 替换容器..."
ENV_FILE="$LATEST_DIR/.env"
COMPOSE_FILE="$LATEST_DIR/docker-compose.yaml"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down --rmi local
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d

# ---------- 等待容器就绪 ----------
echo "  等待容器启动..."
for i in $(seq 1 15); do
    if docker exec "$CONTAINER_NAME" python manage.py check --database default > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# ---------- 3) migrate ----------
echo ""
echo "[3/3] 执行 migrate..."
docker exec "$CONTAINER_NAME" python manage.py makemigrations
docker exec "$CONTAINER_NAME" python manage.py migrate

# ---------- 重载 nginx（可选）----------
if [ "$NO_NGINX" -eq 0 ] && [ -f "$NGINX_RELOAD_DIR/reload.sh" ]; then
    echo ""
    echo "重载 nginx..."
    bash "$NGINX_RELOAD_DIR/reload.sh"
fi

echo ""
echo "======== 更新完成 ========"
