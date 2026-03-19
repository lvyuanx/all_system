#!/usr/bin/env python3
"""生成 nginx 站点配置。

用法：在打包产物目录执行
  python register_nginx.py -p <nginx_port>

读取同目录 .env 获取 IMAGE_PORT / HOST_DATA，并输出 all_system_<nginx_port>.conf。
- nginx 监听 <nginx_port>
- 反代到容器暴露的主机端口 IMAGE_PORT（容器内 8000）
- 静态/媒体目录指向 HOST_DATA/IMAGE_PORT 路径
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

REQUIRED_ENV = ["IMAGE_TAG", "IMAGE_PORT"]
DEFAULT_HOST_DATA = "/data/all_system"
NGINX_CONF_DIR = Path("/etc/nginx/conf.d")

template = """server {{
    listen {nginx_port};
    listen [::]:{nginx_port};

    server_name _;

    location /static/ {{
        alias {host_data}/{app_port}/oss/static/;
        autoindex off;
        expires 30d;
        access_log off;
        add_header Cache-Control "public";
    }}

    location /media/ {{
        alias {host_data}/{app_port}/oss/media/;
        autoindex off;
        expires 30d;
        access_log off;
        add_header Cache-Control "public";
    }}

    location / {{
        proxy_pass http://127.0.0.1:{app_port};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
    }}
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


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 nginx 站点配置")
    parser.add_argument("-p", "--port", type=int, required=True, help="nginx 监听端口")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    env_file = here / ".env"
    if not env_file.exists():
        raise FileNotFoundError(f"未找到 .env: {env_file}")

    env = parse_env(env_file)
    app_port = env["IMAGE_PORT"]
    host_data = env.get("HOST_DATA", DEFAULT_HOST_DATA)

    conf_text = template.format(
        nginx_port=args.port,
        app_port=app_port,
        host_data=host_data,
    )

    out_path = here / f"all_system_{args.port}.conf"
    out_path.write_text(conf_text, encoding="utf-8")
    print(f"已生成: {out_path}")

    # 复制到 /etc/nginx/conf.d（若不存在才复制），并重载 nginx
    if NGINX_CONF_DIR.exists():
        dest = NGINX_CONF_DIR / out_path.name
        if dest.exists():
            print(f"已存在，未覆盖: {dest}")
        else:
            try:
                shutil.copy2(out_path, dest)
                print(f"已复制到: {dest}")
                reload_cmds = [
                    ["systemctl", "reload", "nginx"],
                    ["nginx", "-s", "reload"],
                ]
                reloaded = False
                for cmd in reload_cmds:
                    try:
                        subprocess.run(cmd, check=True)
                        print(f"已重载 nginx: {' '.join(cmd)}")
                        reloaded = True
                        break
                    except Exception:
                        continue
                if not reloaded:
                    print("未能自动重载 nginx，请手动执行 reload", file=sys.stderr)
            except PermissionError:
                print(f"缺少权限，无法复制到 {dest}", file=sys.stderr)
    else:
        print(f"未找到 nginx conf 目录: {NGINX_CONF_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
