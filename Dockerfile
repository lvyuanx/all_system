FROM python:3.11-slim

WORKDIR /app

# 写入国内 Debian 源（阿里云）
RUN echo "deb https://mirrors.aliyun.com/debian trixie main contrib non-free" > /etc/apt/sources.list \
 && echo "deb https://mirrors.aliyun.com/debian trixie-updates main contrib non-free" >> /etc/apt/sources.list \
 && echo "deb https://mirrors.aliyun.com/debian-security trixie-security main contrib non-free" >> /etc/apt/sources.list

# 安装 mysqlclient 编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# 拷贝 requirements.txt 并安装 Python 库
COPY requirements.txt .

RUN pip install --upgrade pip \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com

RUN pip install -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com

# 拷贝整个项目
COPY . .

# 使用你的自定义启动命令 uvserver
CMD ["python", "manage.py", "uvserver"]