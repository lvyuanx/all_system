# -*-coding:utf-8 -*-

"""
# File       : site_address_list_view.py
# Time       : 2026-01-13 20:11:46
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 分页查询站点地址列表
"""

from typing import List

from django.db.models import QuerySet, Q

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.utils import common_util
from site_mgmt.models import SiteAddress
from staff.models import Staff

from . import schemas


class Pagination(AsyncLimitOffsetPagination):
    
    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        """过滤数据，根据前端传入的参数进行过滤"""
        search = input_filter.get("search")
        if search:  # 搜索条件为空
            queryset = queryset.filter(
                Q(site_person_in_charge__full_name__contains=search) |
                Q(contact_number__contains=search)
            )

        site_id = input_filter.get("site_id")
        if site_id:  # 站点ID
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
    finally_code = "000", "分页查询站点地址列表失败"
    response_schema = schemas.SiteAddressListItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        cur_user = await common_util.get_user_async(request)
        if cur_user.is_superuser:  # 获取所有站点地址
            querset = SiteAddress.objects.all()
        else:

            staff_data = (
                await Staff.objects.filter(user=cur_user).values("site_id").afirst()
            )
            site_id = staff_data.get("site_id")

            querset = SiteAddress.objects.filter(site_id=site_id)

        return querset.values(
            "site_person_in_charge__full_name",
            "address_province__name",
            "address_city__name",
            "address_district__name",
            "address_detail",
            "site__site_name",
            "contact_number",
        )
