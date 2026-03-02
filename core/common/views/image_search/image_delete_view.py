# -*-coding:utf-8 -*-

"""
# File       : image_delete_view.py
# Time       : 2026-03-02 09:20:33
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 删除指定图片
"""

from ninja import Query
from core.common.image_search_engine import get_image_search_manager
from core.ninja_extra.api_extra import BaseApi, HttpRequest


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "删除指定图片失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest, image_name: str = Query(..., description="图片名称"), group: str = Query(default=None, description="图库分组名称")):
        image_search_manager = get_image_search_manager()
        image_search_manager.delete_image(image_name)