# -*-coding:utf-8 -*-

"""
# File       : order_create_view.py
# Time       : 2026-01-28 22:55:27
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 创建订单
"""
from decimal import Decimal
from asgiref.sync import sync_to_async
from ninja import Body
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.models import Order, OrderItem
from django.db import transaction
from site_mgmt.utils import site_util
from . import schemas


def do_create(request: HttpRequest, data: schemas.OrderCreateSchema):
    
        total_amount = Decimal("0")
        discount_amount = Decimal("0")
        for item in data.items:
            total_amount += item.unit_price * item.count
            discount_amount += item.discount_price
        
        with transaction.atomic():
            order = Order(
                order_type=data.order_type,
                total_amount=total_amount,
                discount_amount=discount_amount,
                payable_amount=total_amount - discount_amount,
                shipping_party=data.shipping_party,
                shipping_party_company=data.shipping_party_company,
                shipping_party_phone=data.shipping_party_phone,
                shipping_party_address=data.shipping_party_address,
                receiver_name=data.receiver_name,
                receiver_phone=data.receiver_phone,
                receiver_address=data.receiver_address,
                receiver_company=data.receiver_company,
                delivery_method=data.delivery_method,
                memo=data.memo,
                site_id=data.site_id,
                create_user=request.user
            )
            order.save()

            for item in data.items:
                order_item = OrderItem(
                    order=order,
                    pattern_code=item.pattern_code,
                    color=item.color,
                    unit_price=item.unit_price,
                    count=item.count,
                    total_unit=item.total_unit,
                    discount_price=item.discount_price,
                    memo = item.memo
                )
                order_item.save()

class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "创建订单失败"
    response_schema = None
    error_codes = [
        ("001", "请最少添加一个订单项"),
        ("002", "您没有该站点的订单创建权限"),
    ]

    

    @staticmethod
    async def api(request: HttpRequest, data: schemas.OrderCreateSchema = Body(...)):
        if not data.items:
            # 订单项不能为空
            raise BusinessException("002")
        
        cur_sites = await site_util.aget_cur_sites(request)
        if data.site_id not in [item.pk for item in cur_sites]:
            # 站点权限校验
            raise BusinessException("002")

        await sync_to_async(do_create)(data=data, request=request)