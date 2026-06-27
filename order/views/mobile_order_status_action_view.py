# -*-coding:utf-8 -*-

"""
# File       : mobile_order_status_action_view.py
# Description: 移动端订单状态操作
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from order.enums import OrderStatusChoices
from order.machine import OrderStateMachine
from order.models import Order
from order.services import ensure_order_cancel_memo, ensure_order_cancel_user, ensure_order_confirm_user
from order.signals.signals import order_canceled_signal, order_complete_signal
from site_mgmt.utils import site_util

from . import schemas


ACTION_MAP = {
    "cancel": {
        "trigger": "cancel",
        "allowed_status": [OrderStatusChoices.CREATED, OrderStatusChoices.CONFIRMED],
        "signal": order_canceled_signal,
    },
    "confirm": {
        "trigger": "confirm",
        "allowed_status": [OrderStatusChoices.CREATED],
        "signal": None,
    },
    "schedule": {
        "trigger": "schedule",
        "allowed_status": [OrderStatusChoices.CONFIRMED],
        "signal": None,
    },
    "start_production": {
        "trigger": "start_production",
        "allowed_status": [OrderStatusChoices.SCHEDULED],
        "signal": None,
    },
    "finish_production": {
        "trigger": "finish_production",
        "allowed_status": [OrderStatusChoices.PRODUCING],
        "signal": None,
    },
    "complete": {
        "trigger": "complete",
        "allowed_status": [OrderStatusChoices.SHIPPED],
        "signal": order_complete_signal,
    },
}


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单状态操作失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "不支持的操作"),
        ("003", "当前订单状态[{status_name}]无法进行该操作"),
        ("004", "该订单暂未分配确认人"),
        ("005", "只有该订单指定确认人可以确认"),
        ("006", "只有订单创建人或确认人可以取消订单"),
        ("007", "取消订单必须填写备注"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.OrderStatusActionSchema = Body(..., description="订单状态操作")
    ):
        order_manager = Order.objects.filter(pk=data.order_id, is_delete=False)
        order_manager = await sync_to_async(site_util.admin_filter_site)(request, order_manager)
        if not await order_manager.aexists():
            raise BusinessException("001")

        order = await order_manager.afirst()

        action_cfg = ACTION_MAP.get(data.action)
        if not action_cfg:
            raise BusinessException("002")

        if order.order_status not in action_cfg["allowed_status"]:
            raise BusinessException(
                "003",
                {"status_name": OrderStatusChoices(order.order_status).label},
            )
        if data.action == "cancel":
            ensure_order_cancel_user(order, request.user)
            data.operator_memo = ensure_order_cancel_memo(data.operator_memo)
        if data.action == "confirm":
            ensure_order_confirm_user(order, request.user)

        sm = OrderStateMachine(order, request.user, data.operator_memo)
        if data.action == "finish_production":
            allowed, _ = sm.can_finish_production()
            if not allowed:
                raise BusinessException("003", {"status_name": "生产中(流程未完成)"})
        getattr(sm, action_cfg["trigger"])()
        sm.save_state()

        if action_cfg["signal"] is not None:
            action_cfg["signal"].send(sender=Order, instance=order)
