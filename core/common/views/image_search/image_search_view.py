# -*-coding:utf-8 -*-

"""
# File       : iamge_search_view.py
# Time       : 2026-03-02 09:23:46
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 以图搜图
"""
from ninja import Query
from core.common.image_search_engine import get_image_search_manager
from core.ninja_extra.api_extra import BaseApi, HttpRequest, UploadedFile, File
from .. import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "以图搜图失败"
    response_schema = list[schemas.ImageSearchResultListItemSchema]
    error_codes = []

    @staticmethod
    async def api(
        request: HttpRequest,
        image: UploadedFile = File(...),
        top_k: int = Query(5, description="搜索结果数量"),
        group: str | None = Query(default=None, description="图库分组名称"),
    ):
        image_search_manager = get_image_search_manager()
        return image_search_manager.search(
            image.file.read(),
            top_k=top_k,
            group=group,
        )

            
