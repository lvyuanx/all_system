# -*-coding:utf-8 -*-

"""
# File       : config_util.py
# Time       : 2025-07-24 21:15:16
# Author     : lyx
# version    : python 3.11
# Description: 配置工具类
"""
import importlib
import os
from core.exceptions import SysConfigException, SysException

def load_config_dict():
    """
    从环境变量加载配置模块并提取配置字典。
    只包含非内置变量（排除 __name__ 等）。
    """
    config_path = os.environ.get('DJANGO_CONFIG_MODULE')
    if not config_path:
        return {}

    try:
        config_module = importlib.import_module(config_path)
        return {
            k: v for k, v in config_module.__dict__.items()
            if not k.startswith('__')
        }
    except ModuleNotFoundError as e:
        raise SysException(f"配置模块无法导入: {config_path}") from e

# 初始化配置字典
config_dict = load_config_dict()

def merge_config(settings_param: str, default=None):
    """
    获取配置值，优先从配置模块中获取，否则使用默认值。

    :param settings_param: 配置项名称
    :param default: 默认值（可选）
    :return: 配置值
    :raises: SysConfigException 如果配置项不存在且无默认值
    """
    if settings_param in config_dict:
        return config_dict[settings_param]
    
    if default is not None:
        return default

    raise SysConfigException(settings_param)
