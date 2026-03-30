#!/usr/bin/env python3
"""生成 nginx 站点配置。

用法：在打包产物目录执行
  python register_nginx.py --listen 80
  python register_nginx.py --server-name dev_all_system.lvyx.cc --listen 80
  python register_nginx.py --server-name dev_all_system.lvyx.cc --https

读取同目录 .env 获取 IMAGE_PROJECT / IMAGE_SITE / HOST_DATA / IMAGE_DOMAIN / SERVER_NAME。
- nginx 监听 listen 端口（默认 80）
- 可选生成 443 SSL 站点（默认启用，可用 --no-https 关闭）
- 反代到容器 <project>_<site>:8000
- 静态/媒体目录指向 HOST_DATA/<site> 路径
"""
import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional

REQUIRED_ENV = ["IMAGE_SITE"]
DEFAULT_PROJECT = "all_system"
DEFAULT_DATA_ROOT = "/data"
DEFAULT_SSL_CERT = "/etc/nginx/ssl/fullchain.pem"
DEFAULT_SSL_KEY = "/etc/nginx/ssl/privkey.pem"
NGINX_CONF_DIR = Path("/home/applications/ng_container/nginx/conf.d")

LOCATION_BLOCK = """    location /static/ {{
        alias {host_data}/{site}/oss/static/;
        autoindex off;
        expires 30d;
        access_log off;
        add_header Cache-Control "public";
    }}

    location /media/ {{
        alias {host_data}/{site}/oss/media/;
        autoindex off;
        expires 30d;
        access_log off;
        add_header Cache-Control "public";
    }}

    location / {{
        proxy_pass http://{project}_{site}:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
    }}
"""

HTTP_TEMPLATE = """server {{
    listen {listen_port};
    listen [::]:{listen_port};

    server_name {server_name};

{locations}
}}
"""

HTTPS_TEMPLATE = """server {{
    listen {listen_port} ssl;
    listen [::]:{listen_port} ssl;

    server_name {server_name};

    ssl_certificate     {ssl_cert};
    ssl_certificate_key {ssl_key};

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

{locations}
}}
"""


def parse_env(path: Path) -> Dict[str, str]:
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


def validate_site(site: str) -> str:
    if "/" in site or "\\" in site:
        raise ValueError("IMAGE_SITE 不能包含路径分隔符")
    return site


def validate_project(project: str) -> str:
    if "/" in project or "\\" in project:
        raise ValueError("IMAGE_PROJECT 不能包含路径分隔符")
    return project


def normalize_domain(domain: str) -> str:
    return domain.strip().lstrip(".")


def resolve_host_data(env: Dict[str, str], project: str) -> Path:
    host_data = env.get("HOST_DATA")
    if host_data:
        return Path(host_data)
    return Path(DEFAULT_DATA_ROOT) / project


def build_server_name(
    site: str,
    project: str,
    server_name: Optional[str],
    root_domain: Optional[str],
) -> str:
    if server_name:
        return server_name
    if root_domain:
        slug = f"{site}-{project}".replace("_", "-")
        return f"{slug}.{normalize_domain(root_domain)}"
    return "_"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 nginx 站点配置")
    parser.add_argument(
        "-p",
        "--listen",
        type=int,
        default=80,
        help="nginx 监听端口，默认 80",
    )
    parser.add_argument(
        "--https",
        dest="https",
        action="store_true",
        default=True,
        help="生成 443 SSL 配置（默认启用）",
    )
    parser.add_argument(
        "--no-https",
        dest="https",
        action="store_false",
        help="仅生成 80 配置",
    )
    parser.add_argument(
        "--server-name",
        "--domain",
        dest="server_name",
        default=None,
        help="server_name（可选），优先于 .env 的 SERVER_NAME",
    )
    parser.add_argument(
        "--root-domain",
        default=None,
        help="根域名（可选），用于生成 <site>_<project>.<domain>",
    )
    parser.add_argument(
        "--ssl-cert",
        default=None,
        help=f"SSL fullchain 路径，默认 {DEFAULT_SSL_CERT} 或 .env 的 SSL_CERT",
    )
    parser.add_argument(
        "--ssl-key",
        default=None,
        help=f"SSL 私钥路径，默认 {DEFAULT_SSL_KEY} 或 .env 的 SSL_KEY",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    env_file = here / ".env"
    if not env_file.exists():
        raise FileNotFoundError(f"未找到 .env: {env_file}")

    env = parse_env(env_file)
    project = validate_project(env.get("IMAGE_PROJECT", DEFAULT_PROJECT))
    site = validate_site(env["IMAGE_SITE"])
    host_data = resolve_host_data(env, project)

    root_domain = args.root_domain or env.get("IMAGE_DOMAIN")
    server_name = build_server_name(site, project, args.server_name or env.get("SERVER_NAME"), root_domain)

    locations = LOCATION_BLOCK.format(
        site=site,
        project=project,
        host_data=host_data,
    )

    blocks = []
    blocks.append(HTTP_TEMPLATE.format(
        listen_port=args.listen,
        server_name=server_name,
        locations=locations,
    ))
    if args.https:
        ssl_cert = args.ssl_cert or env.get("SSL_CERT") or DEFAULT_SSL_CERT
        ssl_key = args.ssl_key or env.get("SSL_KEY") or DEFAULT_SSL_KEY
        blocks.append(HTTPS_TEMPLATE.format(
            listen_port=443,
            server_name=server_name,
            ssl_cert=ssl_cert,
            ssl_key=ssl_key,
            locations=locations,
        ))

    conf_text = "\n\n".join(blocks)

    out_path = here / f"{project}_{site}.conf"
    out_path.write_text(conf_text, encoding="utf-8")
    print(f"已生成 {out_path}")

    # 复制到 nginx conf.d（若不存在才复制）
    if NGINX_CONF_DIR.exists():
        dest = NGINX_CONF_DIR / out_path.name
        if dest.exists():
            print(f"已存在，未覆盖 {dest}")
        else:
            try:
                shutil.copy2(out_path, dest)
                print(f"已复制到: {dest}")
            except PermissionError:
                print(f"缺少权限，无法复制到 {dest}", file=sys.stderr)
    else:
        print(f"未找到 nginx conf 目录: {NGINX_CONF_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
