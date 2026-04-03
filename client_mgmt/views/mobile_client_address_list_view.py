# -*-coding:utf-8 -*-

"""
# File       : mobile_client_address_list_view.py
# Description: 移动端分页查询客户地址
"""

from typing import List

from django.db.models import QuerySet, Q
from ninja import Body

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.utils import common_util
from client_mgmt.models import Client
from site_mgmt.utils import site_util

from . import schemas


class Pagination(AsyncLimitOffsetPagination):
    InputSource = Body

    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        search = input_filter.get("search")
        if search:
            queryset = queryset.filter(
                Q(client_name__contains=search) | Q(client_phone__contains=search)
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
    finally_code = "000", "移动端分页查询客户地址失败"
    response_schema = schemas.ClientAddressListItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        queryset = Client.objects.filter(is_active=True)
        cur_user = await common_util.get_user_async(request)
        if cur_user.is_superuser:
            qs = queryset
        else:
            sites = await site_util.aget_cur_sites(request)
            site_ids = [s.pk for s in sites]
            if not site_ids:
                qs = queryset.none()
            else:
                qs = queryset.filter(sites__in=site_ids)

        return qs.values(
            "client_name",
            "client_phone",
            "company_name",
            "address_province__name",
            "address_city__name",
            "address_district__name",
            "address_detail",
        )
