# -*-coding:utf-8 -*-

"""
# File       : get_city_view.py
# Time       : 2025-10-17 15:42:08
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 获取市
"""
from typing import Any, Dict
from django.db.models import QuerySet

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from ..models import CityCode
from . import schemas


class Pagination(AsyncLimitOffsetPagination):
    async def afilter_queryset(self, queryset: QuerySet[CityCode, Dict[str, Any]], input_filter: Dict):
        """
        按前端传入的 filter 字典筛选
        """
        parent_id = input_filter.get("parent_id")
        if parent_id:
            queryset = queryset.filter(province=parent_id)
        
        return queryset


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "获取市失败"
    response_schema = schemas.AddressLevelItemSchema
    error_codes = []
    is_pagination: bool = True
    pagination_class = Pagination

    @staticmethod
    async def api(request: HttpRequest):
        return CityCode.objects.all().values("id", "code", "name")