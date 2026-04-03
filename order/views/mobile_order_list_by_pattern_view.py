# -*-coding:utf-8 -*-

"""
# File       : mobile_order_list_by_pattern_view.py
# Description: 移动端按版号分页查询关联订单
"""

from asgiref.sync import sync_to_async
from django.db.models import QuerySet

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from order.enums import OrderStatusChoices
from order.models import Order, OrderItem
from site_mgmt.utils import site_util

from . import schemas


class Pagination(AsyncLimitOffsetPagination):

    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        pattern_code = input_filter.get("pattern_code")
        if not pattern_code:
            return queryset.none()
        order_ids = OrderItem.objects.filter(
            pattern_code=pattern_code,
            is_delete=False,
        ).values_list("order_id", flat=True)
        return queryset.filter(pk__in=order_ids)

    async def aprocess_result(self, results: list) -> list:
        for item in results:
            item["order_status_str"] = (
                OrderStatusChoices(item["order_status"]).label
                if item.get("order_status")
                else ""
            )
        return results


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    finally_code = "000", "移动端按版号查询订单失败"
    response_schema = schemas.OrderListByPatternItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        qs = (
            Order.objects.filter(is_delete=False)
            .values(
                "pk",
                "order_no",
                "order_status",
                "receiver_name",
                "receiver_phone",
                "payable_amount",
                "paid_amount",
            )
            .order_by("-pk")
        )
        qs = await sync_to_async(site_util.admin_filter_site)(request, qs)
        return qs


class OrderModuleView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    finally_code = "000", "移动端按版号查询订单失败"
    response_schema = schemas.OrderListByPatternItemSchema
    is_pagination = True
    pagination_class = Pagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        qs = (
            Order.objects.filter(is_delete=False)
            .values(
                "pk",
                "order_no",
                "order_status",
                "receiver_name",
                "receiver_phone",
                "payable_amount",
                "paid_amount",
            )
            .order_by("-pk")
        )
        qs = await sync_to_async(site_util.admin_filter_site)(request, qs)
        return qs
