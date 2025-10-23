# -*-coding:utf-8 -*-

"""
# File       : init_sys.py
# Time       : 2025-10-15 23:12:18
# Author     : lyx
# version    : python 3.11
# Description: 初始化系统，首次部署系统时执行，请勿重复执行
"""
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from core.utils import module_util


logger = logging.getLogger(__name__)
INIT_SCRIPTS = settings.INIT_SCRIPTS

class Command(BaseCommand):
    help = "使用uvicorn启动服务"

    def add_arguments(self, parser):
        pass
    
    def handle(self, *args, **options):
        if not INIT_SCRIPTS:
            logger.warning("未配置初始化脚本")
        
        with transaction.atomic():
            for script in INIT_SCRIPTS:
                logger.info(f"正在执行初始化脚本：{script} ...")
                script_func = module_util.import_from_path(script)
                script_func()