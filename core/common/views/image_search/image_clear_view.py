# -*-coding:utf-8 -*-

"""
# File       : image_clear_view.py
# Time       : 2026-03-10 10:00:54
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 清空图库
"""

from ninja import Query
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.common.image_search import image_search_adapter


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["DELETE"]
    finally_code = "000", "清空图库失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest, group: str = Query("default", description="图片分组")):
        await image_search_adapter.image_clear(group)