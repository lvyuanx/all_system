# -*-coding:utf-8 -*-

"""
# File       : mobile_order_list_view.py
# Description: 移动端订单分页查询
"""

from typing import Any

from asgiref.sync import sync_to_async
from django.db.models import Q, QuerySet, F, OuterRef, Subquery
from ninja import Body

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.utils import time_util, common_util
from order.enums import (
    OrderPayStatusChoices,
    OrderShipStatusChoices,
    OrderStatusChoices,
    OrderTypeChoices,
)
from order.models import Order, OrderItem
from pattern_library.models import Pattern
from site_mgmt.utils import site_util

from . import schemas


class Pagination(AsyncLimitOffsetPagination):
    InputSource = Body

    @staticmethod
    def _normalize_list(value: Any) -> list:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    @staticmethod
    def _to_datetime(value: Any):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return time_util.timestamp_to_datetime(int(value))
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            if cleaned.isdigit():
                return time_util.timestamp_to_datetime(int(cleaned))
            try:
                return time_util.str_to_datetime(cleaned)
            except Exception:
                return None
        return None

    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        if not input_filter:
            return queryset

        search = input_filter.get("search") or input_filter.get("q")
        if search:
            queryset = queryset.filter(
                Q(order_no__contains=search)
                | Q(receiver_name__contains=search)
                | Q(receiver_phone__contains=search)
            )

        order_no = input_filter.get("order_no")
        if order_no:
            queryset = queryset.filter(order_no__contains=order_no)

        receiver_name = input_filter.get("receiver_name")
        if receiver_name:
            queryset = queryset.filter(receiver_name__contains=receiver_name)

        receiver_phone = input_filter.get("receiver_phone")
        if receiver_phone:
            queryset = queryset.filter(receiver_phone__contains=receiver_phone)

        receiver_company = input_filter.get("receiver_company")
        if receiver_company:
            queryset = queryset.filter(receiver_company__contains=receiver_company)

        order_status = self._normalize_list(input_filter.get("order_status"))
        if order_status:
            queryset = queryset.filter(order_status__in=order_status)

        pay_status = self._normalize_list(input_filter.get("pay_status"))
        if pay_status:
            queryset = queryset.filter(pay_status__in=pay_status)

        ship_status = self._normalize_list(input_filter.get("ship_status"))
        if ship_status:
            queryset = queryset.filter(ship_status__in=ship_status)

        order_type = self._normalize_list(input_filter.get("order_type"))
        if order_type:
            queryset = queryset.filter(order_type__in=order_type)

        site_id = self._normalize_list(input_filter.get("site_id"))
        if site_id:
            queryset = queryset.filter(site_id__in=site_id)

        create_time_start = self._to_datetime(
            input_filter.get("create_time_start") or input_filter.get("start_time")
        )
        if create_time_start:
            queryset = queryset.filter(create_time__gte=create_time_start)

        create_time_end = self._to_datetime(
            input_filter.get("create_time_end") or input_filter.get("end_time")
        )
        if create_time_end:
            queryset = queryset.filter(create_time__lte=create_time_end)

        return queryset

    async def aprocess_result(self, results: list) -> list:
        for item in results:
            item["order_status_str"] = (
                OrderStatusChoices(item["order_status"]).label
                if item.get("order_status") is not None
                else ""
            )
            item["pay_status_str"] = (
                OrderPayStatusChoices(item["pay_status"]).label
                if item.get("pay_status") is not None
                else ""
            )
            item["ship_status_str"] = (
                OrderShipStatusChoices(item["ship_status"]).label
                if item.get("ship_status") is not None
                else ""
            )
            item["order_type_str"] = (
                OrderTypeChoices(item["order_type"]).label
                if item.get("order_type") is not None
                else ""
            )
            item["create_time_str"] = (
                time_util.datetime_to_str(item["create_time"])
                if item.get("create_time")
                else ""
            )
            item["main_image"] = common_util.media_url(item.get("main_image", ""))
        return results


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单列表查询失败"
    response_schema = schemas.MobileOrderListItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        first_pattern_main_image_subquery = (
            OrderItem.objects.filter(order_id=OuterRef("pk"), is_delete=False)
            .annotate(
                pattern_main_image=Subquery(
                    Pattern.objects.filter(
                        code=OuterRef("pattern_code"),
                        is_delete=False,
                        is_active=True,
                    ).values("main_image__file")[:1]
                )
            )
            .order_by("pk")
            .values("pattern_main_image")[:1]
        )
        qs = (
            Order.objects.filter(is_delete=False)
            .annotate(main_image=Subquery(first_pattern_main_image_subquery))
            .values(
                "order_no",
                "order_type",
                "order_status",
                "pay_status",
                "ship_status",
                "payable_amount",
                "paid_amount",
                "receiver_name",
                "receiver_phone",
                "receiver_company",
                "create_time",
                order_id=F("pk"),
                main_image=F("main_image"),
            )
            .order_by("-pk")
        )
        qs = await sync_to_async(site_util.admin_filter_site)(request, qs)
        return qs
