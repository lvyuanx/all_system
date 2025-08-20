# -*-coding:utf-8 -*-

"""
# File       : uvserver.py
# Time       : 2025-04-21 13:40:13
# Author     : lyx
# version    : python 3.11
# Description: 使用uvicorn作为服务器
"""
import logging
import socket

from django.core.management.base import BaseCommand
from core.conf import settings


logger = logging.getLogger(__name__)
NINJA_BASE_URL = settings.NINJA_BASE_URL
start_template = r"""




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
{admin_url}
{ip_admin_url}

推荐使用在线文档进行接口调试：
{doc_url}
{ip_doc_url}

"""

def start_print(**kwargs):
    logger.info(start_template.format(**kwargs))


class Command(BaseCommand):
    help = "使用uvicorn启动服务"

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


        # 获取本机的主机名
        hostname = socket.gethostname()
        # 获取主机的ip地址
        ip_address = socket.gethostbyname(hostname)
        
        url_prefix = f"http://{'127.0.0.1' if options['host'] == '0.0.0.0' else '127.0.0.1' }:{options['port']}"
        url_ip_prefix = f"http://{ip_address}:{options['port']}"
        
        start_print(
            **options,
            doc_url = f"{url_prefix}/{NINJA_BASE_URL}docs",
            ip_doc_url = f"{url_ip_prefix}/{NINJA_BASE_URL}docs",
            admin_url = f"{url_prefix}/admin/",
            ip_admin_url = f"{url_ip_prefix}/admin/",
        )

        uvicorn.run(
            f"{asgi_module}:{asgi_application}",
            host=options["host"],
            port=options["port"],
            workers=options["workers"],
            reload=options["reload"],
            loop=options["loop"],
            log_level=options["log_level"] or ("DEBUG" if settings.DEBUG else "INFO"),
            log_config=settings.LOGGING
        )

