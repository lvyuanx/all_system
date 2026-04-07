# -*-coding:utf-8 -*-

"""
# File       : mobile_client_list_view.py
# Description: 移动端分页查询客户信息（只读）
"""

from decimal import Decimal
from typing import List

from asgiref.sync import sync_to_async
from django.db.models import QuerySet, Q, F
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
                Q(client_name__contains=search)
                | Q(client_phone__contains=search)
                | Q(company_name__contains=search)
            )

        company_name = input_filter.get("company_name")
        if company_name:
            queryset = queryset.filter(company_name__contains=company_name)

        site_id = input_filter.get("site_id")
        if site_id:
            queryset = queryset.filter(sites=site_id)

        return queryset

    async def aprocess_result(self, results: List) -> List:
        client_ids = [item.get("client_id") for item in results if item.get("client_id") is not None]
        site_names_map: dict[int, list[str]] = {}
        if client_ids:
            site_rows = await sync_to_async(list)(
                Client.objects.filter(pk__in=client_ids)
                .values("id", "sites__site_name")
                .order_by("id")
            )
            for row in site_rows:
                client_id = row.get("id")
                site_name = row.get("sites__site_name")
                if client_id is None or not site_name:
                    continue
                names = site_names_map.setdefault(client_id, [])
                if site_name not in names:
                    names.append(site_name)

        rst = []
        for item in results:
            province = item.get("address_province__name", "") or ""
            city = item.get("address_city__name", "") or ""
            district = item.get("address_district__name", "") or ""
            detail = item.get("address_detail", "") or ""
            total_order_count = int(item.get("total_order_count") or 0)
            total_end_order_count = int(item.get("total_end_order_count") or 0)
            sex = item.get("client_sex") or Client.Gender.UNKNOWN
            try:
                sex_str = Client.Gender(sex).label
            except Exception:
                sex_str = ""

            rst.append(
                {
                    "client_id": item.get("client_id"),
                    "client_name": item.get("client_name", ""),
                    "client_phone": item.get("client_phone"),
                    "client_sex": sex,
                    "client_sex_str": sex_str,
                    "client_age": item.get("client_age"),
                    "company_name": item.get("company_name"),
                    "company_phone": item.get("company_phone"),
                    "company_logo": common_util.media_url(item.get("company_logo_file", "")),
                    "full_address": province + city + district + detail,
                    "total_amount": float(item.get("total_amount") or Decimal("0")),
                    "total_arrears": float(item.get("total_arrears") or Decimal("0")),
                    "total_order_count": total_order_count,
                    "total_end_order_count": total_end_order_count,
                    "unfinished_order_total": total_order_count - total_end_order_count,
                    "site_names": site_names_map.get(item.get("client_id"), []),
                }
            )
        return rst


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端分页查询客户信息失败"
    response_schema = schemas.MobileClientListItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        queryset = Client.objects.filter(is_active=True)
        cur_user = await common_util.get_user_async(request)
        if not cur_user.is_superuser:
            sites = await site_util.aget_cur_sites(request)
            site_ids = [s.pk for s in sites]
            if not site_ids:
                queryset = queryset.none()
            else:
                queryset = queryset.filter(sites__in=site_ids)

        return queryset.distinct().values(
            "client_name",
            "client_phone",
            "client_sex",
            "client_age",
            "company_name",
            "company_phone",
            "address_province__name",
            "address_city__name",
            "address_district__name",
            "address_detail",
            "total_amount",
            "total_arrears",
            "total_order_count",
            "total_end_order_count",
            client_id=F("pk"),
            company_logo_file=F("company_logo"),
        )
