# -*-coding:utf-8 -*-

"""
# File       : order_info_view.py
# Time       : 2026-02-04 22:17:32
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 根据ID查询订单信息
"""
from asgiref.sync import sync_to_async
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from . import schemas
from order.models import Order, OrderItem
from core.utils import common_util
from site_mgmt.utils import site_util
from django.db.models import F


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "根据ID查询订单信息失败"
    response_schema = schemas.OrderInfoSchema
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
            raise BusinessException("001")

        
        order_obj = await order_manager.values(
            "site_id",
            "order_type",
            "shipping_party",
            "shipping_party_phone",
            "shipping_party_address",
            "shipping_party_company",
            "delivery_method",
            "receiver_name",
            "receiver_phone",
            "receiver_address",
            "receiver_company",
            "memo",
            order_id=F("pk"),
        ).afirst()
        
        item_manager = OrderItem.objects.filter(
            order_id=order_id,
            is_delete=False
        ).values(
            "pattern_code",
            "color",
            "count",
            "unit_price",
            "discount_price",
            "total_unit",
            "memo",
        )
        items = [item async for item in item_manager]

        order_obj["items"] = items
        return schemas.OrderInfoSchema(**order_obj)
        
        