#!/usr/bin/env python3
"""一键构建 all_system 镜像并产出离线包。

产出结构：
  build/<TAG>/<project>.tar
  build/<TAG>/docker-compose.yaml
  build/<TAG>/.env   （包含 IMAGE_PROJECT、IMAGE_SITE、IMAGE_TAG、HOST_DATA、LOG_PATH、IMAGE_DOMAIN、SERVER_NAME）

特性：
- 支持 -s/--site 指定子域名/站点标识，写入 .env
- 支持 -p/--project 指定项目名，数据目录为 /data/<project>/<site>
- 可选 --domain 指定根域名，自动生成 SERVER_NAME=<site>_<project>.<domain>
- 镜像内已包含代码（Dockerfile 已 COPY . /app）
- 可在任意目录调用（内部使用绝对路径）
"""
import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT_DIR / "docker" / "Dockerfile"
COMPOSE_FILE = ROOT_DIR / "docker" / "docker-compose.yaml"
SOURCE_CONFIG = ROOT_DIR / "main" / "config.py"
SOURCE_OSS_MEDIA = ROOT_DIR / "oss" / "media" / "system"
SOURCE_OSS_STATIC = ROOT_DIR / "oss" / "static"
INIT_TEMPLATE = ROOT_DIR / "run" / "linuxsvr" / "init.py"
NGINX_SCRIPT = ROOT_DIR / "run" / "linuxsvr" / "register_nginx.py"
DEFAULT_PROJECT = "all_system"
DEFAULT_BUILD_DIR = ROOT_DIR / "build"
DEFAULT_DATA_ROOT = "/data"


def run(cmd: List[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建 all_system 镜像并生成离线包")
    parser.add_argument(
        "-s",
        "--site",
        "-site",
        required=True,
        help="子域名/站点标识，例如 dev",
    )
    parser.add_argument(
        "-p",
        "--project",
        "-project",
        default=DEFAULT_PROJECT,
        help=f"项目名，默认 {DEFAULT_PROJECT}",
    )
    parser.add_argument(
        "-d",
        "--domain",
        "-domain",
        default=None,
        help="根域名（可选），如 lvyx.cc，将生成 <site>_<project>.<domain>",
    )
    parser.add_argument(
        "-t",
        "--tag",
        default=None,
        help="镜像标签/输出目录名，默认使用时间戳",
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
        help="输出根目录，默认在项目 build/",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help=f"宿主机数据根目录，默认 /data/<project>",
    )
    return parser.parse_args()


def validate_site(site: str) -> str:
    if "/" in site or "\\" in site:
        raise ValueError("site 不能包含路径分隔符")
    return site


def validate_project(project: str) -> str:
    if "/" in project or "\\" in project:
        raise ValueError("project 不能包含路径分隔符")
    return project


def normalize_domain(domain: str) -> str:
    return domain.strip().lstrip(".")


def resolve_host_data(project: str, data_dir: Optional[str]) -> str:
    if data_dir:
        return data_dir
    return f"{DEFAULT_DATA_ROOT}/{project}"


def build_server_name(site: str, project: str, domain: Optional[str]) -> Optional[str]:
    if not domain:
        return None
    normalized = normalize_domain(domain)
    return f"{site}_{project}.{normalized}"


def write_env(
    env_path: Path,
    tag: str,
    project: str,
    site: str,
    data_dir: str,
    domain: Optional[str],
    server_name: Optional[str],
) -> None:
    log_path = f"{data_dir}/{site}/logs"
    env_content = (
        f"IMAGE_TAG={tag}\n"
        f"IMAGE_PROJECT={project}\n"
        f"IMAGE_SITE={site}\n"
        f"HOST_DATA={data_dir}\n"
        f"LOG_PATH={log_path}\n"
    )
    if domain:
        env_content += f"IMAGE_DOMAIN={normalize_domain(domain)}\n"
    if server_name:
        env_content += f"SERVER_NAME={server_name}\n"
    env_path.write_text(env_content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    site = validate_site(args.site)
    project = validate_project(args.project)
    tag = args.tag or datetime.now().strftime("%Y%m%d%H%M%S")

    host_data = resolve_host_data(project, args.data_dir)
    server_name = build_server_name(site, project, args.domain)

    # 1) 构建镜像
    build_cmd = [
        "docker",
        "build",
        "-f",
        str(DOCKERFILE),
        "-t",
        f"{project}:{tag}",
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
    tar_path = target_dir / f"{project}.tar"
    save_cmd = [
        "docker",
        "save",
        "-o",
        str(tar_path),
        f"{project}:{tag}",
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

    # 6) 复制 oss/media/system/** 和 oss/static/**
    oss_media_dest = target_dir / "oss" / "media" / "system"
    if SOURCE_OSS_MEDIA.exists():
        oss_media_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SOURCE_OSS_MEDIA, oss_media_dest)
    else:
        print(f"警告: 未找到 {SOURCE_OSS_MEDIA}，未复制 oss 媒体资源")

    oss_static_dest = target_dir / "oss" / "static"
    if SOURCE_OSS_STATIC.exists():
        oss_static_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SOURCE_OSS_STATIC, oss_static_dest)
    else:
        print(f"警告: 未找到 {SOURCE_OSS_STATIC}，未复制 oss 静态资源")

    # 7) 写 .env（project、site、tag、宿主机数据根）
    env_path = target_dir / ".env"
    write_env(env_path, tag, project, site, host_data, args.domain, server_name)

    # 8) 复制 init.py
    init_dest = target_dir / "init.py"
    if INIT_TEMPLATE.exists():
        shutil.copy2(INIT_TEMPLATE, init_dest)
    else:
        print(f"警告: 未找到 {INIT_TEMPLATE}，未复制 init.py")

    # 9) 复制 register_nginx.py
    nginx_script_dest = target_dir / "register_nginx.py"
    if NGINX_SCRIPT.exists():
        shutil.copy2(NGINX_SCRIPT, nginx_script_dest)
    else:
        print(f"警告: 未找到 {NGINX_SCRIPT}，未复制 register_nginx.py")

    print(
        "打包完成\n"
        f"镜像: {project}:{tag}\n"
        f"输出目录: {target_dir}\n"
        "包含: <project>.tar, docker-compose.yaml, .env, config.py, init.py, register_nginx.py, oss/media/system/**, oss/static/**\n"
        "部署示例: python init.py；生成 nginx 配置: python register_nginx.py --server-name <domain> [--listen 80]"
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
