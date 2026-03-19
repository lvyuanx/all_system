#!/usr/bin/env python3
"""一键构建 all_system 镜像并产出离线包。

产出结构：
  build/<TAG>/all_system.tar
  build/<TAG>/docker-compose.yaml
  build/<TAG>/.env   （包含 IMAGE_PORT、IMAGE_TAG）

特性：
- 支持 -p/--port 指定对外映射端口（默认 27001），写入 .env。
- 镜像内已包含代码（Dockerfile 已 COPY . /app）。
- 可在任意目录调用（内部使用绝对路径）。
"""
import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT_DIR / "docker" / "Dockerfile"
COMPOSE_FILE = ROOT_DIR / "docker" / "docker-compose.yaml"
SOURCE_CONFIG = ROOT_DIR / "main" / "config.py"
SOURCE_OSS = ROOT_DIR / "oss" / "media" / "system"
INIT_TEMPLATE = ROOT_DIR / "run" / "linuxsvr" / "init.py"
IMAGE_NAME = "all_system"
DEFAULT_BUILD_DIR = ROOT_DIR / "build"
HOST_DATA_DEFAULT = "/data/all_system"


def run(cmd: List[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建 all_system 镜像并生成离线包")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=27001,
        help="对外暴露端口，映射到容器 8000",
    )
    parser.add_argument(
        "-t",
        "--tag",
        default=None,
        help="镜像标签/产出目录名，默认使用时间戳",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="构建镜像时使用 --no-cache",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_BUILD_DIR),
        help="产出根目录，默认在项目 build/",
    )
    parser.add_argument(
        "--data-dir",
        default=HOST_DATA_DEFAULT,
        help=f"宿主机数据根目录，默认 {HOST_DATA_DEFAULT}，将按端口号分子目录",
    )
    return parser.parse_args()


def write_env(env_path: Path, tag: str, port: int, data_dir: str) -> None:
    log_path = f"{data_dir}/{port}/logs"
    env_content = (
        f"IMAGE_TAG={tag}\n"
        f"IMAGE_PORT={port}\n"
        f"HOST_DATA={data_dir}\n"
        f"LOG_PATH={log_path}\n"
    )
    env_path.write_text(env_content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    tag = args.tag or datetime.now().strftime("%Y%m%d%H%M%S")

    # 1) 构建镜像
    build_cmd = [
        "docker",
        "build",
        "-f",
        str(DOCKERFILE),
        "-t",
        f"{IMAGE_NAME}:{tag}",
    ]
    if args.no_cache:
        build_cmd.append("--no-cache")
    build_cmd.append(str(ROOT_DIR))
    run(build_cmd)

    # 2) 准备输出目录
    base_dir = Path(args.output).expanduser()
    if not base_dir.is_absolute():
        base_dir = (Path.cwd() / base_dir).resolve()
    target_dir = base_dir / tag
    target_dir.mkdir(parents=True, exist_ok=True)

    # 3) 保存镜像为 tar
    tar_path = target_dir / "all_system.tar"
    save_cmd = [
        "docker",
        "save",
        "-o",
        str(tar_path),
        f"{IMAGE_NAME}:{tag}",
    ]
    run(save_cmd)

    # 4) 复制 docker-compose.yaml
    compose_dest = target_dir / "docker-compose.yaml"
    shutil.copy2(COMPOSE_FILE, compose_dest)

    # 5) 复制 config.py
    config_dest = target_dir / "config.py"
    if SOURCE_CONFIG.exists():
        shutil.copy2(SOURCE_CONFIG, config_dest)
    else:
        print(f"警告: 未找到 {SOURCE_CONFIG}，未复制 config.py")

    # 6) 复制 oss/media/system/**
    oss_dest = target_dir / "oss" / "media" / "system"
    if SOURCE_OSS.exists():
        oss_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SOURCE_OSS, oss_dest)
    else:
        print(f"警告: 未找到 {SOURCE_OSS}，未复制 oss 媒体资源")

    # 7) 写 .env（端口、tag、宿主机数据根）
    env_path = target_dir / ".env"
    write_env(env_path, tag, args.port, args.data_dir)

    # 8) 复制 init.py
    init_dest = target_dir / "init.py"
    if INIT_TEMPLATE.exists():
        shutil.copy2(INIT_TEMPLATE, init_dest)
    else:
        print(f"警告: 未找到 {INIT_TEMPLATE}，未复制 init.py")

    print(
        "打包完成\n"
        f"镜像: {IMAGE_NAME}:{tag}\n"
        f"输出目录: {target_dir}\n"
        "包含: all_system.tar, docker-compose.yaml, .env, config.py, init.py, oss/media/system/**\n"
        "部署示例: python init.py"
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
