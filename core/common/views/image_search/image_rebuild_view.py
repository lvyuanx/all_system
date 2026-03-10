# -*-coding:utf-8 -*-

"""
# File       : image_rebuild_view.py
# Time       : 2026-03-10 09:32:38
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 重置图库索引
"""

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.common.image_search import image_search_adapter


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "重置图库索引失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        await image_search_adapter.rebuild()