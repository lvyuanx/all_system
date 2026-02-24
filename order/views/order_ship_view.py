# -*-coding:utf-8 -*-

"""
# File       : order_ship_view.py
# Time       : 2026-02-23 21:10:05
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 订单发货
"""
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.db import transaction
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from order.enums import OrderPayStatusChoices, OrderStatusChoices
from order.models import Order
from order.machine import OrderStateMachine
from . import schemas


@transaction.atomic
def do(request: HttpRequest, order: Order, delivery_method: int, tracking_no: str, shipping_fee: Decimal):
    order.delivery_method = delivery_method
    order.tracking_no = tracking_no
    order.shipping_fee = shipping_fee
    # 订单应付金额 = 订单实付金额 + 运费
    order.payable_amount = order.paid_amount + shipping_fee
    order.update_pay_status()
    order.save()

    sm = OrderStateMachine(order, request.user)
    sm.ship()
    sm.save_state()

    


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["PUT"]
    finally_code = "000", "订单发货失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单状态[{status_name}]下无法进行发货操作！"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.OrderShipSchema = Body(..., description="订单发货信息")):
        try:
            order = await Order.objects.aget(pk=data.order_id)
        except Order.DoesNotExist:
            raise BusinessException("001")
        
        if order.order_status != OrderStatusChoices.FINISHED:
            raise BusinessException("002", {"status_name": OrderStatusChoices(order.order_status).label})
        
        await sync_to_async(do)(request, order, data.delivery_method, data.tracking_no, data.shipping_fee)