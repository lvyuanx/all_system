# 使用官方 Python 3.11 镜像（体积较小的 slim 版本）
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app


# 复制项目依赖文件
COPY requirements.txt .

RUN pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/


# 容器默认启动命令（可按需修改）
CMD ["python manage.py uvserver"]