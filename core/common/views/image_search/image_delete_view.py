# -*-coding:utf-8 -*-

"""
# File       : image_delete_view.py
# Time       : 2026-03-10 10:29:39
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 从图库中删除图片
"""
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.common.image_search import image_search_adapter


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["DELETE"]
    finally_code = "000", "从图库中删除图片失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest, name: str = Query(..., description="图片名称")):
        await image_search_adapter.image_delete(name)