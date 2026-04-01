# -*-coding:utf-8 -*-

"""
# File       : mobile_pattern_list_view.py
# Description: 移动端分页查询版式（模糊搜索）
"""

from typing import List

from django.db.models import Q, QuerySet
from ninja import Body

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.utils import common_util
from pattern_library.models import Pattern

from . import schemas


class Pagination(AsyncLimitOffsetPagination):
    
    InputSource = Body

    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        if "is_active" in input_filter:
            queryset = queryset.filter(is_active=input_filter["is_active"])

        search = input_filter.get("search")
        if search:
            queryset = queryset.filter(
                Q(memo__contains=search) |
                Q(code__contains=search) |
                Q(tags__contains=search)
            )
        return queryset

    async def aprocess_result(self, results: List) -> List:
        rst = []
        for item in results:
            rst.append(
                {
                    "pattern_id": item.get("id", ""),
                    "main_image": common_util.media_url(
                        item.get("main_image__file", "")
                    ),
                    "pattern_code": item.get("code", ""),
                    "pattern_memo": item.get("memo", ""),
                    "tags": [t for t in (item.get("tags", "") or "").split(",") if t],
                }
            )
        return rst


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    finally_code = "000", "分页查询版式失败"
    response_schema = schemas.PatternListItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return (
            Pattern.objects.filter(is_delete=False)
            .order_by("-update_time")
            .values("id", "code", "memo", "tags", "main_image__file")
        )
