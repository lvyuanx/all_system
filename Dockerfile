# syntax=docker/dockerfile:1.6

############################
# 1️⃣ builder 阶段
############################
FROM python:3.11-slim AS builder

WORKDIR /install

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    default-libmysqlclient-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY requirements_linux.txt .

RUN pip install --upgrade pip \
    -i https://mirrors.aliyun.com/pypi/simple/

RUN pip install --no-cache-dir \
    --prefix=/install \
    -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/

RUN pip install --no-cache-dir \
    --prefix=/install \
    -r requirements_linux.txt \
    -i https://mirrors.aliyun.com/pypi/simple/


############################
# 2️⃣ runtime 阶段
############################
FROM python:3.11-slim

WORKDIR /app

# 只装运行时依赖
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

# 🔥 不 COPY 代码
# 代码通过 volume 挂载

CMD ["python", "manage.py", "uvserver"]