# -*-coding:utf-8 -*-

"""
# File       : mobile_order_info_view.py
# Description: 移动端订单详情
"""

from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db.models import F, OuterRef, Subquery

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.utils import time_util, common_util
from order.enums import (
    OrderDeliveryChoices,
    OrderPayStatusChoices,
    OrderShipStatusChoices,
    OrderStatusChoices,
    OrderTypeChoices,
)
from order.models import Order, OrderItem
from pattern_library.models import Pattern
from site_mgmt.utils import site_util

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "移动端订单详情查询失败"
    response_schema = schemas.MobileOrderInfoSchema
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "暂无该订单查看权限"),
    ]

    @staticmethod
    async def api(request: HttpRequest, order_id: int = Query(..., description="订单ID")):
        order_manager = Order.objects.filter(pk=order_id, is_delete=False)
        if not await order_manager.aexists():
            raise BusinessException("001")

        order_manager = await sync_to_async(site_util.admin_filter_site)(request, order_manager)
        if not await order_manager.aexists():
            raise BusinessException("002")

        order_obj = await order_manager.values(
            "order_no",
            "order_type",
            "order_status",
            "pay_status",
            "ship_status",
            "total_amount",
            "discount_amount",
            "shipping_fee",
            "payable_amount",
            "paid_amount",
            "shipping_party",
            "shipping_party_company",
            "shipping_party_phone",
            "shipping_party_address",
            "delivery_method",
            "delivery_time",
            "tracking_no",
            "receiver_name",
            "receiver_phone",
            "receiver_company",
            "receiver_address",
            "memo",
            "create_time",
            order_id=F("pk"),
        ).afirst()

        order_obj["order_status_str"] = (
            OrderStatusChoices(order_obj["order_status"]).label
            if order_obj.get("order_status") is not None
            else ""
        )
        order_obj["pay_status_str"] = (
            OrderPayStatusChoices(order_obj["pay_status"]).label
            if order_obj.get("pay_status") is not None
            else ""
        )
        order_obj["ship_status_str"] = (
            OrderShipStatusChoices(order_obj["ship_status"]).label
            if order_obj.get("ship_status") is not None
            else ""
        )
        order_obj["order_type_str"] = (
            OrderTypeChoices(order_obj["order_type"]).label
            if order_obj.get("order_type") is not None
            else ""
        )
        order_obj["delivery_method_str"] = (
            OrderDeliveryChoices(order_obj["delivery_method"]).label
            if order_obj.get("delivery_method") is not None
            else ""
        )
        order_obj["create_time_str"] = (
            time_util.datetime_to_str(order_obj["create_time"])
            if order_obj.get("create_time")
            else ""
        )

        item_manager = OrderItem.objects.filter(
            order_id=order_id,
            is_delete=False,
        ).annotate(
            main_image=Subquery(
                Pattern.objects.filter(
                    code=OuterRef("pattern_code"),
                    is_delete=False,
                    is_active=True,
                ).values("main_image__file")[:1]
            )
        ).values(
            "item_no",
            "pattern_code",
            "color",
            "count",
            "unit_price",
            "discount_price",
            "total_unit",
            "memo",
            item_id=F("pk"),
            main_image=F("main_image"),
        )

        items = []
        async for item in item_manager:
            total = (item.get("unit_price") or Decimal("0")) * (item.get("count") or 0)
            discount_price = item.get("discount_price") or Decimal("0")
            item["total"] = total
            item["subtotal"] = total - discount_price
            item["main_image"] = common_util.media_url(item.get("main_image", ""))
            items.append(item)

        order_obj["items"] = items
        return schemas.MobileOrderInfoSchema(**order_obj)
