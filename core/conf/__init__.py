# -*-coding:utf-8 -*-

"""
# File       : __init__.py
# Time       : 2025-07-25 15:07:23
# Author     : lyx
# version    : python 3.11
# Description: 增强模块配置默认值
"""
from django.conf import settings as django_settings
from . import default_settings
from core.exceptions import SysConfigException

class Settings:
    
    def __getattr__(self, name):
        if hasattr(django_settings, name):
            return getattr(django_settings, name)
        
        if hasattr(default_settings, name):
            return getattr(default_settings, name)
        
        raise SysConfigException(name)


settings = Settings()
        