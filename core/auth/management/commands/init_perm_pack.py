# -*-coding:utf-8 -*-

"""
# File       : init_perm_pack.py
# Time       : 2025-08-12 13:46:37
# Author     : lyx
# version    : python 3.11
# Description: 初始化权限包
"""
from django.core.management.base import BaseCommand
from core.utils import perm_util

class Command(BaseCommand):
    help = "使用uvicorn启动服务"
    
    
    def handle(self, *args, **options):
        perm_util.init_perm()
