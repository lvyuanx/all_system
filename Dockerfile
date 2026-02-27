# syntax=docker/dockerfile:1.6

FROM python:3.11-slim

WORKDIR /app

# 使用阿里云 Debian 源（bookworm，匹配 python:3.11-slim）
RUN echo "deb https://mirrors.aliyun.com/debian bookworm main contrib non-free" > /etc/apt/sources.list \
 && echo "deb https://mirrors.aliyun.com/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list \
 && echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list

# 安装 mysqlclient 编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# 先拷贝 requirements（利用 Docker 分层缓存）
COPY requirements.txt .
COPY requirements_linux.txt .

# 升级 pip（启用缓存）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com

# 安装 Python 依赖（使用缓存）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements_linux.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com


# 启动命令
CMD ["python", "manage.py", "uvserver"]