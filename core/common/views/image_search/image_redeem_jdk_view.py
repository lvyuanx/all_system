# -*-coding:utf-8 -*-

"""
# File       : image_redeem_jdk_view.py
# Time       : 2026-03-17 23:02:30
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 搜索次数JDK兑换
"""

from ninja import Query
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.common.image_search import image_search_adapter


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "搜索次数JDK兑换失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest, code: str = Query(..., description="兑换码")):
        await image_search_adapter.redeem_jdk(code)