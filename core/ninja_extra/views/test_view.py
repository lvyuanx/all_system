# -*-coding:utf-8 -*-

"""
# File       : test_view.py
# Time       : 2025-07-30 23:04:28
# Author     : lyx
# version    : python 3.11
# Description: 测试
"""
from django.http import Http404
from core.ninja_extra.api_extra import BaseApi, Warning, BusinessException


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_DONE

    finally_code = "000", Warning("测试接口失败")
    response_schema = str

    @staticmethod
    async def api(request):
        # a = 1 / 0
        # raise BusinessException(123)
        return "hello world!!"