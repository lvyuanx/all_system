# -*-coding:utf-8 -*-

"""
# File       : staff_salary_disbursement_list_view.py
# Time       : 2025-09-17 21:20:37
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询其它工资列表信息
"""

from decimal import Decimal
from typing import Any, Dict, List
from django.db.models import Exists, OuterRef, F, QuerySet
from django.forms import DateTimeField
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from staff.models import Staff
from django.db.models import F, Value
from core.utils import time_util
from .. import schemas


class Pagination(AsyncLimitOffsetPagination):
    
    async def aprocess_result(self, results: List) -> List:
        """分页后处理结果，比如序列化或数据脱敏"""
        for item in results:
            item["disbursement_time"] = time_util.now()
            item["actual_disbursement"] = Decimal("0.00")
        return results
    
    async def afilter_queryset(self, queryset: QuerySet[Staff, Dict[str, Any]], input_filter: Dict):
        """
        按前端传入的 filter 字典筛选
        """
        # 基础条件
        full_name = input_filter.get("full_name")
        if full_name:
            queryset = queryset.filter(user__full_name__contains=full_name)

        phone = input_filter.get("phone")
        if phone:
            queryset = queryset.filter(user__phone__contains=phone)

        return queryset


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "查询工资列表信息失败"
    response_schema = schemas.SalaryListItemSchema
    error_codes = []
    is_pagination = True
    pagination_class = Pagination

    @staticmethod
    async def api(request: HttpRequest):
        return Staff.objects.filter(
            user__is_active=True,
        ).annotate(
            sid=F("id"),
            full_name=F("user__full_name"),
            phone=F("user__phone"),
        ).values(
            "sid",
            "staff_code",
            "full_name",
            "phone",
        )
