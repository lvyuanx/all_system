# -*-coding:utf-8 -*-

"""
# File       : order_pay_view.py
# Time       : 2026-02-24 21:59:48
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 订单支付
"""
from asgiref.sync import sync_to_async
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.utils import time_util
from order.models import Order, OrderPayCa
from django.db import transaction
from .. import schemas


@transaction.atomic
def do(request: HttpRequest, data: schemas.OrderPaySchema):
    order_manager = Order.objects.filter(pk=data.order_id)
    if not order_manager.exists():
        raise BusinessException("001")
    
    order = order_manager.first()
    payable_amount = order.payable_amount
    paid_amount = order.paid_amount  

    if payable_amount < (paid_amount + data.pay_amount):
        raise BusinessException("002")
    
    order.paid_amount = paid_amount + data.pay_amount
    pre_status = order.pay_status
    order.update_pay_status()
    order.save()

    user = request.user

    pay_ca = OrderPayCa(
        order_no = order.order_no,
        order = order,
        pre_status = pre_status,
        cur_status = order.pay_status,
        pay_method = data.pay_method,
        pay_amount = data.pay_amount,
        operator = user,
        operator_name = user.full_name,
        operator_phone = user.phone,
        operator_time = time_util.now(),
        operator_memo = data.operator_memo
    )

    pay_ca.save()

    
    

class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "订单支付失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "超过该订单最大可支付金额"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.OrderPaySchema = Body(..., description="订单支付信息")):
        await sync_to_async(do)(request, data)