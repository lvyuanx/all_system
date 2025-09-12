# -*- coding:utf-8 -*-
"""
# File       : orjson_util.py
# Description: orjson 工具方法封装，兼容内置 json 用法
# Author     : you
# Version    : 1.0
"""

import orjson
from typing import Any, Union


def dumps(obj: Any, *, indent: int | None = None, ensure_ascii: bool = False) -> str:
    """
    序列化为 str，类似 json.dumps
    :param obj: 任意对象
    :param indent: 缩进，默认 None（紧凑格式）
    :param ensure_ascii: 是否转义非 ASCII 字符，默认 False（保持中文等原样）
    """
    option = 0
    if indent is not None:
        option |= orjson.OPT_INDENT_2
    if not ensure_ascii:
        option |= orjson.OPT_APPEND_NEWLINE  # 只是让输出更美观（最后多一行）
        option |= orjson.OPT_NON_STR_KEYS    # 支持非 str 键
    return orjson.dumps(obj, option=option).decode("utf-8")


def dumps_bytes(obj: Any, *, indent: int | None = None, ensure_ascii: bool = False) -> bytes:
    """
    序列化为 bytes
    """
    option = 0
    if indent is not None:
        option |= orjson.OPT_INDENT_2
    if not ensure_ascii:
        option |= orjson.OPT_NON_STR_KEYS
    return orjson.dumps(obj, option=option)


def loads(s: Union[str, bytes]) -> Any:
    """
    反序列化，类似 json.loads
    """
    if isinstance(s, str):
        s = s.encode("utf-8")
    return orjson.loads(s)


# 提供一个命名空间，模拟内置 json
class _JsonNamespace:
    dumps = staticmethod(dumps)
    loads = staticmethod(loads)


# 可像标准库一样用 json.dumps / json.loads
json = _JsonNamespace()
