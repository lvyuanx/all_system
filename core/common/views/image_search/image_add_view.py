# -*-coding:utf-8 -*-

"""
# File       : image_add_view.py
# Time       : 2026-03-09 22:58:45
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 图库添加图片
"""

from ninja import Query
from core.common.utils import res_util
from core.ninja_extra.api_extra import BaseApi, HttpRequest, UploadedFile, File
from core.common.image_search import image_search_adapter


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "图库添加图片失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(
        request: HttpRequest,
        file: UploadedFile = File(..., description="图片"),
        group: str = Query("default", description="图片分组"),
    ):
        md5 = res_util.calc_file_md5(file)
        await image_search_adapter.image_add(file, md5, group)
