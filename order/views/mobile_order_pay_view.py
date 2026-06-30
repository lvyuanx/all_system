# -*-coding:utf-8 -*-

"""
# File       : mobile_order_pay_view.py
# Description: 移动端订单支付
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from order.models import Order
from order.views.pay.order_pay_view import do as do_pay
from site_mgmt.utils import site_util

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单支付失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "超过该订单最大可支付金额"),
        ("003", "暂无订单支付权限"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.OrderPaySchema = Body(..., description="订单支付信息")):
        order_manager = Order.objects.filter(pk=data.order_id, is_delete=False)
        order_manager = await sync_to_async(site_util.admin_filter_site)(request, order_manager)
        if not await order_manager.aexists():
            raise BusinessException("001")

        await sync_to_async(do_pay)(request, data)
