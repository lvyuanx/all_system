# -*-coding:utf-8 -*-

"""
# File       : image_lib_init_view.py
# Time       : 2026-03-02 16:10:23
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 初始化图库
"""

from core.common.image_search_engine import get_image_search_engine
from core.ninja_extra.api_extra import BaseApi, HttpRequest


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "初始化图库失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        image_search_engine = get_image_search_engine()
        image_search_engine.rebuild_gallery()
        