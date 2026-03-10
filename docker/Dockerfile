# syntax=docker/dockerfile:1.6

############################
# 1️⃣ builder 阶段
############################
FROM python:3.11.8-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /install

# 使用阿里源
RUN rm -rf /etc/apt/sources.list.d/* \
    && echo "deb https://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 安装编译依赖
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements_linux.txt .

# 升级 pip
RUN pip install --upgrade pip \
    -i https://mirrors.aliyun.com/pypi/simple/

# 安装 Python 依赖（使用缓存）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    --prefix=/install \
    -r requirements.txt \
    -r requirements_linux.txt \
    -i https://mirrors.aliyun.com/pypi/simple/

# 删除 tests 减小体积
RUN find /install -type d -name "tests" -exec rm -rf {} + || true


############################
# 2️⃣ runtime 阶段
############################
FROM python:3.11.8-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 使用阿里源
RUN rm -rf /etc/apt/sources.list.d/* \
    && echo "deb https://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 运行时依赖
RUN apt-get update && apt-get install -y \
    libmariadb3 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 拷贝已安装 Python 包
COPY --from=builder /install /usr/local

# 默认运行
CMD ["python", "manage.py", "uvserver"]