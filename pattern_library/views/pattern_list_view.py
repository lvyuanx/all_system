# -*-coding:utf-8 -*-

"""
# File       : pattern_list_view.py
# Time       : 2026-01-21 22:22:29
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 分页查询版式
"""

from typing import List

from django.db.models import Q, QuerySet

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.utils import common_util
from pattern_library.models import Pattern

from . import schemas


class Pagination(AsyncLimitOffsetPagination):
    
    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        """过滤数据，根据前端传入的参数进行过滤"""
        search = input_filter.get("search")
        if not search:  # 搜索条件为空
            return queryset
        queryset = queryset.filter(
            Q(memo__contains=search) |
            Q(code__contains=search)
        )
        return queryset

    async def aprocess_result(self, results: List) -> List:
        rst = []
        for item in results:
            rst.append(
                {
                    "main_image": common_util.media_url(
                        item.get("main_image__file", "")
                    ),
                    "pattern_code": item.get("code", ""),
                    "pattern_memo": item.get("memo", ""),
                }
            )

        return rst


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "分页查询版式失败"
    response_schema = schemas.PatternListItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return Pattern.objects.filter(is_active=True, is_delete=True).values("code", "memo", "main_image__file")
