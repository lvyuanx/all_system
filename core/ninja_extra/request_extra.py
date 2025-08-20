# -*-coding:utf-8 -*-

"""
# File       : request_extra.py
# Time       : 2025-07-28 22:08:11
# Author     : lyx
# version    : python 3.11
# Description: 注解扩展
"""

from functools import wraps


def api(
    
):
    async def decorator(func):
        @wraps(func)        
        async def wrapper(request, *args, **kwargs):
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator