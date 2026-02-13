# -*-coding:utf-8 -*-

"""
# File       : common_util.py
# Time       : 2025-08-01 00:16:16
# Author     : lyx
# version    : python 3.11
# Description: 通用工具类
"""
import builtins
import importlib
import threading
from decimal import Decimal
from typing import Type

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user
from django.db import models
from django.http import HttpRequest

from core.common.schemas import ChoicesListItemSchema


def import_func_or_class(path: str):
    """
    动态导入类、函数或异常。支持以下格式：
    - "core.xxx.yyy.ClassName"              导入类或函数
    - "core.xxx.yyy:func_name"              明确模块与函数分隔
    - "Exception"                           支持内建异常类自动导入（如 Exception、ValueError）
    - "builtins.Exception"                  显式导入内建异常
    """
    # 特殊处理：只输入 Exception 等内置异常名称
    if '.' not in path and ':' not in path:
        if hasattr(builtins, path):
            return getattr(builtins, path)
        raise ImportError(f"Cannot resolve '{path}' as built-in")

    # 支持冒号方式（模块:属性）
    if ':' in path:
        module_path, attr_path = path.split(':', 1)
    else:
        module_path, attr_path = path.rsplit('.', 1)

    module = importlib.import_module(module_path)
    obj = module

    # 支持链式属性访问，例如 ClassName.attr
    for attr in attr_path.split('.'):
        obj = getattr(obj, attr)

    return obj


def to_decimal(value, digits="0.00"):
    return Decimal(str(value or 0)).quantize(Decimal(digits))


def media_url(path_or_res):
    from django.conf import settings
    if not path_or_res: return ""
    if isinstance(path_or_res, str):
        return f"{settings.MEDIA_URL}{path_or_res}"
    else:
        #  Resource 对象
        return path_or_res.file.url


class SingletonBase:
    _instance = None
    _lock = threading.Lock()  # 保证线程安全

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # 初始化参数只在第一次实例化时生效
                    cls._instance._init(*args, **kwargs)
        return cls._instance
    
    
    def _init(*args, **kwargs):
        raise NotImplementedError("单例子类必须实现 _init 方法而不是 __init__ 方法")


async def get_user_async(request: HttpRequest):
    return await sync_to_async(get_user, thread_sensitive=True)(request)


def choices_to_schema(
    enum: Type[models.Choices],
) -> list[ChoicesListItemSchema]:
    """
    将 Django models.Choices / TextChoices / IntegerChoices
    转换为 Schema 列表
    """
    return [
        ChoicesListItemSchema(
            name=choice.name,
            value=choice.value,
            label=choice.label,
        )
        for choice in enum
    ]
