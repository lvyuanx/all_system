# -*-coding:utf-8 -*-

"""
# File       : mobile_site_address_list_view.py
# Description: 移动端分页查询站点地址列表
"""

from typing import List

from asgiref.sync import sync_to_async
from django.db.models import QuerySet, Q
from ninja import Body

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from site_mgmt.models import SiteAddress
from site_mgmt.utils import site_util

from . import schemas


class Pagination(AsyncLimitOffsetPagination):
    InputSource = Body

    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        search = input_filter.get("search")
        if search:
            queryset = queryset.filter(
                Q(site_person_in_charge__full_name__contains=search)
                | Q(contact_number__contains=search)
            )

        site_id = input_filter.get("site_id")
        if site_id:
            queryset = queryset.filter(site_id=site_id)
        return queryset

    async def aprocess_result(self, results: List) -> List:
        rst = []
        for item in results:
            rst.append(
                {
                    "shipping_party": item.get("site_person_in_charge__full_name", ""),
                    "shipping_party_company": item.get("site__site_name", ""),
                    "shipping_party_phone": item.get("contact_number", ""),
                    "shipping_party_address": item.get("address_province__name", "")
                    + item.get("address_city__name", "")
                    + item.get("address_district__name", "")
                    + item.get("address_detail", ""),
                }
            )

        return rst


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端分页查询站点地址列表失败"
    response_schema = schemas.SiteAddressListItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        queryset = SiteAddress.objects.all()
        queryset = await sync_to_async(site_util.admin_filter_site)(
            request, queryset, site_field_name="site"
        )
        return queryset.values(
            "site_person_in_charge__full_name",
            "address_province__name",
            "address_city__name",
            "address_district__name",
            "address_detail",
            "site__site_name",
            "contact_number",
        )
