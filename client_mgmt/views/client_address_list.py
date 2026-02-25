# -*-coding:utf-8 -*-

"""
# File       : client_address_list.py
# Time       : 2026-01-15 22:45:51
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 分页查询客户地址
"""

from typing import List

from django.db.models import QuerySet, Q

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.utils import common_util
from staff.models import Staff
from . import schemas
from client_mgmt.models import Client


class Pagination(AsyncLimitOffsetPagination):
    
    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        """过滤数据，根据前端传入的参数进行过滤"""
        search = input_filter.get("search")
        if search:  # 搜索条件为空
            queryset = queryset.filter(
                Q(client_name__contains=search) |
                Q(client_phone__contains=search)
            )

        site_id = input_filter.get("site_id")
        if site_id:
            queryset = queryset.filter(sites=site_id)
        return queryset

    async def aprocess_result(self, results: List) -> List:
        rst = []
        for item in results:
            rst.append(
                {
                    "receiver_name": item.get("client_name", ""),
                    "receiver_company": item.get("company_name", ""),
                    "receiver_phone": item.get("client_phone", ""),
                    "receiver_address": item.get("address_province__name", "")
                    + item.get("address_city__name", "")
                    + item.get("address_district__name", "")
                    + item.get("address_detail", ""),
                }
            )

        return rst


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "分页查询客户地址失败"
    response_schema = schemas.ClientAddressListItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        cur_user = await common_util.get_user_async(request)
        queryset = Client.objects.filter(is_active=True).values(
            "client_name",
            "client_phone",
            "company_name",
            "address_province__name",
            "address_city__name",
            "address_district__name",
            "address_detail",
        )
        if cur_user.is_superuser:  # 获取所有站点地址
            querset = queryset.all()
        else:
            staff_data = (
                await Staff.objects.filter(user=cur_user).values("site_id").afirst()
            )
            site_id = staff_data.get("site_id")
            querset = queryset.filter(
                site_id=site_id
            )
        
        return querset
        