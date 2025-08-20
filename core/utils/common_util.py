# -*-coding:utf-8 -*-

"""
# File       : common_util.py
# Time       : 2025-08-01 00:16:16
# Author     : lyx
# version    : python 3.11
# Description: 通用工具类
"""
import importlib


import importlib
import builtins

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
