# -*-coding:utf-8 -*-

"""
# File       : uvserver.py
# Time       : 2025-04-21 13:40:13
# Author     : lyx
# version    : python 3.11
# Description: 使用uvicorn作为服务器
"""
import asyncio
import logging
import socket

from django.core.management.base import BaseCommand
from core.conf import settings


logger = logging.getLogger(__name__)
NINJA_BASE_URL = settings.NINJA_BASE_URL
start_template = r"""

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DJANGO + UVICORN <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 ______  __       __          ____    __    __  ____       
/\  _  \/\ \     /\ \        /\  _`\ /\ \  /\ \/\  _`\     
\ \ \L\ \ \ \    \ \ \       \ \,\L\_\ `\`\\/'/\ \,\L\_\   
 \ \  __ \ \ \  __\ \ \  __   \/_\__ \`\ `\ /'  \/_\__ \   
  \ \ \/\ \ \ \L\ \\ \ \L\ \    /\ \L\ \`\ \ \    /\ \L\ \ 
   \ \_\ \_\ \____/ \ \____/    \ `\____\ \ \_\   \ `\____\
    \/_/\/_/\/___/   \/___/      \/_____/  \/_/    \/_____/
                                                           
                                                           
                                                           
                              _ooOoo_                               
                             o8888888o                              
                             88" . "88                              
                             (| ^_^ |)                              
                             O\  =  /O                              
                          ____/`---'\____                           
                        .'  \\|     |//  `.                         
                       /  \\|||  :  |||//  \                        
                      /  _||||| -:- |||||-  \                       
                      |   | \\\  -  /// |   |                       
                      | \_|  ''\---/''  |   |                       
                      \  .-\__  `-`  ___/-. /                       
                    ___`. .'  /--.--\  `. . ___                     
                  ."" '<  `.___\_<|>_/___.'  >'"".                  
                | | :  `- \`.;`\ _ /`;.`/ - ` : | |                 
                \  \ `-.   \_ __\ /__ _/   .-` /  /                 
          ========`-.____`-.___\_____/___.-`____.-'========         
                               `=---='                              
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^        
                佛祖保佑       永不宕机     永无BUG                 

IP: {host}, Port: {port}, Workers: {workers}, Reload: {reload}, Loop: {loop}
管理后台地址:
- {admin_url}
- {ip_admin_url}

推荐使用在线文档进行接口调试：
- {doc_url}
- {ip_doc_url}

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> STARTED <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

"""


class Command(BaseCommand):
    help = "使用uvicorn启动服务"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asgi_module = None
        self.asgi_application = None
        self.host = None
        self.port = None
        self.workers = None
        self.reload = None
        self.loop = None
        self.log_level = None
        self.ip_address = None
        self.ready_event = asyncio.Event()

    def add_arguments(self, parser):

        parser.add_argument(
            "--host",
            default="0.0.0.0",
            type=str,
            help="Host",
        )
        parser.add_argument(
            "--port",
            default=8000,
            type=int,
            help="Port",
        )
        parser.add_argument(
            "--workers",
            default=1,
            type=int,
            help="启动的进程数量, 默认1",
        )
        parser.add_argument(
            "--reload",
            action="store_true",
            default=False,
            help="开启热更新",
        )
        parser.add_argument(
            "--loop",
            default="auto",
            type=str,
            help="选择事件循环, 默认auto",
        )
        parser.add_argument(
            "--log-level",
            default="info",
            type=str,
            help="日志等级, 默认info",
            choices=["critical", "error", "warning", "info", "debug", "trace"],
        )
        parser.add_argument(
            "--log-config",
            default=getattr(settings, "LOGGING_CONFIG", None),
            type=str,
            help="日志配置文件, 默认为None",
        )

    def handle(self, *args, **options):
        import uvicorn

        ASGI_APPLICATION = getattr(settings, "ASGI_APPLICATION")
        assert ASGI_APPLICATION, "ASGI_APPLICATION not found in settings"
        LOGGING = getattr(settings, "LOGGING")
        assert LOGGING, "LOGGING not found in settings"
        asgi_module, asgi_application = ASGI_APPLICATION.rsplit(".", 1)

        self.asgi_module = asgi_module
        self.asgi_application = asgi_application
        self.host = options["host"]
        self.port = options["port"]
        self.workers = options["workers"]
        self.reload = options["reload"]
        self.loop = options["loop"]
        self.log_level = options["log_level"]

        self.ip_address = self._get_local_ip_address()

        asyncio.run(self._start())

    def _get_local_ip_address(self):
        # macOS may return a hostname that is not resolvable unless it is in /etc/hosts.
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return "127.0.0.1" if self.host == "0.0.0.0" else self.host

    async def _start(self):
        tasks = [
            asyncio.create_task(self._run_uvicorn()),
            asyncio.create_task(self._uvicorn_ready_event()),
            asyncio.create_task(self._print_information()),
        ]

        await asyncio.gather(*tasks)

    async def _run_uvicorn(self):
        import uvicorn

        config = uvicorn.Config(
            f"{self.asgi_module}:{self.asgi_application}",
            host=self.host,
            port=self.port,
            loop=self.loop,
            log_level=self.log_level or settings.LOG_LEVEL,
            log_config=settings.LOGGING,
        )

        server = uvicorn.Server(config)

        # 异步启动 uvicorn
        await server.serve()

    async def _uvicorn_ready_event(self, timeout: float = 10.0):
        host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while loop.time() < deadline:
            try:
                reader, writer = await asyncio.open_connection(host, self.port)
                writer.close()
                await writer.wait_closed()
                self.ready_event.set()
                return
            except OSError:
                await asyncio.sleep(0.1)

        raise RuntimeError("Uvicorn 启动超时")

    async def _print_information(self):
        await self.ready_event.wait()
        url_prefix = f"http://{'127.0.0.1' if self.host == '0.0.0.0' else self.host }:{self.port}"
        url_ip_prefix = f"http://{self.ip_address}:{self.port}"
        doc_url = f"{url_prefix}/{NINJA_BASE_URL}docs"
        ip_doc_url = f"{url_ip_prefix}/{NINJA_BASE_URL}docs"
        admin_url = f"{url_prefix}/admin/"
        ip_admin_url = f"{url_ip_prefix}/admin/"

        logger.info(
            start_template.format(
                **{
                    "host": self.host,
                    "port": self.port,
                    "workers": self.workers,
                    "reload": self.reload,
                    "loop": self.loop,
                    "doc_url": doc_url,
                    "ip_doc_url": ip_doc_url,
                    "admin_url": admin_url,
                    "ip_admin_url": ip_admin_url,
                }
            )
        )
