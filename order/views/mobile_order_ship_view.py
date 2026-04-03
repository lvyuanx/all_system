# -*-coding:utf-8 -*-

"""
# File       : mobile_order_ship_view.py
# Description: 移动端订单发货
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from order.enums import OrderStatusChoices
from order.models import Order
from order.views.order_ship_view import do as do_ship
from site_mgmt.utils import site_util

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["PUT"]
    finally_code = "000", "移动端订单发货失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单状态[{status_name}]下无法进行发货操作"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.OrderShipSchema = Body(..., description="订单发货信息")
    ):
        order_manager = Order.objects.filter(pk=data.order_id, is_delete=False)
        order_manager = await sync_to_async(site_util.admin_filter_site)(request, order_manager)
        if not await order_manager.aexists():
            raise BusinessException("001")

        order = await order_manager.afirst()

        if order.order_status != OrderStatusChoices.FINISHED:
            raise BusinessException(
                "002", {"status_name": OrderStatusChoices(order.order_status).label}
            )

        await sync_to_async(do_ship)(
            request,
            order,
            data.delivery_method,
            data.tracking_no,
            data.shipping_fee,
        )
