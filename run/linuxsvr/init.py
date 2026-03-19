#!/usr/bin/env python3
"""部署初始化脚本：基于 .env 配置完成数据目录准备、镜像加载、容器启动。

执行位置：打包产物目录（包含 .env / docker-compose.yaml / all_system.tar / config.py）。
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

REQUIRED_ENV = ["IMAGE_TAG", "IMAGE_PORT"]
DEFAULT_HOST_DATA = "/data/all_system"

def parse_env(path: Path) -> Dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"未找到 .env: {path}")
    env: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    for key in REQUIRED_ENV:
        if key not in env:
            raise ValueError(f".env 缺少 {key}")
    return env


def run(cmd):
    print("$", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def ensure_paths(host_data: Path, port: str) -> Path:
    base = host_data / port
    logs = base / "logs"
    oss = base / "oss"
    base.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    oss.mkdir(parents=True, exist_ok=True)
    return base


def copy_config(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    if not src.exists():
        raise FileNotFoundError(f"源 config.py 不存在: {src}")
    shutil.copy2(src, dst)


def ensure_image(image: str, tar_path: Path) -> None:
    inspect = subprocess.run(["docker", "image", "inspect", image], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if inspect.returncode == 0:
        return
    if not tar_path.exists():
        raise FileNotFoundError(f"镜像不存在且未找到 tar: {tar_path}")
    run(["docker", "load", "-i", str(tar_path)])


def main() -> None:
    here = Path(__file__).resolve().parent
    env_file = here / ".env"
    compose_file = here / "docker-compose.yaml"
    tar_file = here / "all_system.tar"
    config_src = here / "config.py"

    env = parse_env(env_file)
    host_data = Path(env.get("HOST_DATA", DEFAULT_HOST_DATA))
    port = str(env["IMAGE_PORT"])
    image_tag = env["IMAGE_TAG"]
    image = f"all_system:{image_tag}"

    data_base = ensure_paths(host_data, port)
    copy_config(config_src, data_base / "config.py")

    ensure_image(image, tar_file)

    run([
        "docker", "compose",
        "--env-file", str(env_file),
        "-f", str(compose_file),
        "up", "-d",
    ])

    print("完成：数据目录=%s, 端口=%s, 镜像=%s" % (data_base, port, image))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"失败: {exc}", file=sys.stderr)
        sys.exit(1)
