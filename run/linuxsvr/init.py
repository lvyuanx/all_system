#!/usr/bin/env python3
"""部署初始化脚本：基于 .env 完成数据目录准备、镜像加载、容器启动。

执行位置：打包产物目录（包含 .env / docker-compose.yaml / <project>.tar / config.py）。
"""
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

REQUIRED_ENV = ["IMAGE_TAG", "IMAGE_SITE"]
DEFAULT_PROJECT = "all_system"
DEFAULT_DATA_ROOT = "/data"


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


def validate_site(site: str) -> str:
    if "/" in site or "\\" in site:
        raise ValueError("IMAGE_SITE 不能包含路径分隔符")
    return site


def validate_project(project: str) -> str:
    if "/" in project or "\\" in project:
        raise ValueError("IMAGE_PROJECT 不能包含路径分隔符")
    return project


def resolve_host_data(env: Dict[str, str], project: str) -> Path:
    host_data = env.get("HOST_DATA")
    if host_data:
        return Path(host_data)
    return Path(DEFAULT_DATA_ROOT) / project


def ensure_paths(host_data: Path, site: str) -> Path:
    base = host_data / site
    logs = base / "logs"
    oss = base / "oss"
    base.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    oss.mkdir(parents=True, exist_ok=True)
    return base


def copy_oss_dir(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        # 如果目标目录非空则跳过，避免覆盖已有数据
        try:
            next(dst.iterdir())
            return
        except StopIteration:
            shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_config(src: Path, dst: Path) -> None:
    if dst.exists():
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
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


def container_exists(name: str) -> bool:
    proc = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name=^{name}$", "-q"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return bool(proc.stdout.strip())


def resolve_tar_file(here: Path, project: str) -> Path:
    primary = here / f"{project}.tar"
    if primary.exists():
        return primary
    legacy = here / "all_system.tar"
    if legacy.exists():
        return legacy
    return primary


def main() -> None:
    here = Path(__file__).resolve().parent
    env_file = here / ".env"
    compose_file = here / "docker-compose.yaml"
    config_src = here / "config.py"

    env = parse_env(env_file)
    project = validate_project(env.get("IMAGE_PROJECT", DEFAULT_PROJECT))
    site = validate_site(env["IMAGE_SITE"])
    image_tag = env["IMAGE_TAG"]

    host_data = resolve_host_data(env, project)
    image = f"{project}:{image_tag}"
    container_name = f"{project}_{site}"
    tar_file = resolve_tar_file(here, project)

    # 1) 确保镜像存在
    ensure_image(image, tar_file)

    # 2) 若容器存在则 down
    if container_exists(container_name):
        subprocess.run([
            "docker", "compose",
            "--env-file", str(env_file),
            "-f", str(compose_file),
            "down",
        ], check=False)

    # 3) 确保数据目录和 config.py
    data_base = ensure_paths(host_data, site)
    copy_config(config_src, data_base / "config.py")

    # 3b) 同步 oss 静态资源 (oss/**) -> /data/.../oss/（仅当目标为空，避免覆盖自有数据）
    oss_src = here / "oss"
    oss_dst = data_base / "oss"
    copy_oss_dir(oss_src, oss_dst)

    # 4) 启动容器
    run([
        "docker", "compose",
        "--env-file", str(env_file),
        "-f", str(compose_file),
        "up", "-d",
    ])

    print("完成：数据目录=%s, project=%s, site=%s, 镜像=%s" % (data_base, project, site, image))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"失败: {exc}", file=sys.stderr)
        sys.exit(1)
