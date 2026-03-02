# -*-coding:utf-8 -*-

"""
# File       : image_list_view.py
# Time       : 2026-03-02 16:19:33
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查看图库中的所有图片
"""

from ninja import Query
from core.common.image_search_engine import get_image_search_manager
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from .. import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查看图库中的所有图片失败"
    response_schema = schemas.ImageListSchema
    error_codes = []

    @staticmethod
    async def api(
        request: HttpRequest,
        page: int = Query(1, description="页码"),
        page_size: int = Query(10, description="每页数量"),
        original_name: str = Query(None, description="图片名称"),
        group: str = Query(None, description="图库分组名称"),
    ):
        image_search_manager = get_image_search_manager()
        return image_search_manager.list_gallery(group, page, page_size, original_name)
