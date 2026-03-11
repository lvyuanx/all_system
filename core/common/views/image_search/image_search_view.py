# -*-coding:utf-8 -*-

"""
# File       : image_search_view.py
# Time       : 2026-03-10 10:57:24
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 以图搜图
"""

from django.conf import settings
from core.common.utils import res_util
from core.common.views.schemas import ImageSearchResultListItemSchema
from core.ninja_extra.api_extra import BaseApi, HttpRequest, UploadedFile, File, Query
from core.common.image_search import image_search_adapter


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "以图搜图失败"
    response_schema = list[ImageSearchResultListItemSchema]
    error_codes = []

    @staticmethod
    async def api(
        request: HttpRequest,
        file: UploadedFile = File(..., description="图片"),
    ):
        md5 = res_util.calc_file_md5(file)
        res = await image_search_adapter.image_search(file=file, md5=md5, group=settings.IMAGE_SEARCH_GROUP)
        return res
