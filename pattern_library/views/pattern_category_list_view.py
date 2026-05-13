# -*-coding:utf-8 -*-

"""
# File       : pattern_category_list_view.py
# Description: 查询版式类别列表
"""

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from pattern_library.models import PatternCategory

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询版式类别列表失败"
    response_schema = list[schemas.PatternCategorySchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        data = []
        async for item in (
            PatternCategory.objects.filter(is_delete=False, is_active=True)
            .order_by("id")
            .values("id", "name", "code_prefix", "date_mode", "serial_digits")
        ):
            data.append(item)
        return data
