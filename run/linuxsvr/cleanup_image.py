#!/usr/bin/env python3
"""强制删除镜像：如有基于该镜像的容器，先删除容器再删镜像。

用法示例：
  python cleanup_image.py all_system:latest
  python cleanup_image.py all_system:202403 -v  # 同时删除匿名卷
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def run(cmd):
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT_DIR)


def get_containers(image: str):
    cmd = ["docker", "ps", "-a", "-q", "--filter", f"ancestor={image}"]
    print("$", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="强制删除镜像：先删除基于该镜像的容器")
    parser.add_argument("image", help="镜像名:标签，例如 all_system:latest")
    parser.add_argument(
        "-v",
        "--prune-volumes",
        action="store_true",
        help="删除容器时同时删除匿名卷",
    )
    args = parser.parse_args()

    container_ids = get_containers(args.image)
    if container_ids:
        rm_cmd = ["docker", "rm", "-f"]
        if args.prune_volumes:
            rm_cmd.append("-v")
        rm_cmd += container_ids
        run(rm_cmd)
    else:
        print("没有容器使用该镜像")

    run(["docker", "rmi", "-f", args.image])
    print("镜像删除完成")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
