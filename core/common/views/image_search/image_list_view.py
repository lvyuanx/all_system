# -*-coding:utf-8 -*-

"""
# File       : image_list_view.py
# Time       : 2026-03-09 22:01:55
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询图库列表接口
"""

from django.conf import settings
from core.common.views.schemas import ImageResultListItemSchema
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.common.image_search import image_search_adapter
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询图库列表接口失败"
    response_schema = AsyncLimitOffsetPagination.Output[ImageResultListItemSchema]
    error_codes = [

    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        page: int = Query(1, description="页码"),
        page_size: int = Query(20, description="每页数量"),
        keyword: str = Query(None, description="搜索关键词"),
        order: str = Query("desc", description="排序方式"),
    ):
        res = await image_search_adapter.image_list(settings.IMAGE_SEARCH_GROUP, page, page_size, keyword, order)
        return AsyncLimitOffsetPagination.Output(
            current_page=res.get("page"),
            page_size=res.get("page_size"),
            total_count=res.get("total"),
            items=res.get("results"),
        )
