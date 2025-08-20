# -*-coding:utf-8 -*-

"""
# File       : exception_handlers.py
# Time       : 2025-07-31 23:57:06
# Author     : lyx
# version    : python 3.11
# Description: 异常处理
"""
import logging

from django.http import JsonResponse
from core.exceptions.base_exceptions import BaseException
from core.ninja_extra.response_schema import ErrorResponse, BaseLevel, ResponseLevel
from core.status_codes import code_dict

logger = logging.getLogger(__name__)

def base_exception_handler(request, e: BaseException):
    """自定义异常处理"""
    code = e.code
    message = e.message
    if isinstance(message, BaseLevel):
        level = message.level
        message = message.msg
    else:
        level = ResponseLevel.ERROR
    logger.error(f"系统异常 - 错误码:[{code}]; 错误消息:[{message}]")
    return JsonResponse(data=ErrorResponse(code=code, msg=message, level=level).model_dump(), status=200)


def finally_exception_handler(request, e: Exception):
    """最终异常处理"""
    logger.error(f"未知异常",  exc_info=True)
    return JsonResponse(data=ErrorResponse(
        code="1",
        msg=code_dict.get("1", "未知异常")
    ).model_dump(), status=200)