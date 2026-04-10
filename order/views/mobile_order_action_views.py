# -*-coding:utf-8 -*-

"""
# File       : mobile_order_action_views.py
# Description: 移动端订单状态操作（单独接口）
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from order.enums import OrderStatusChoices
from order.machine import OrderStateMachine
from order.models import Order
from order.signals.signals import order_canceled_signal, order_complete_signal
from site_mgmt.utils import site_util

from . import schemas


async def _get_order_with_site_filter(request: HttpRequest, order_id: int) -> Order:
    order_manager = Order.objects.filter(pk=order_id, is_delete=False)
    order_manager = await sync_to_async(site_util.admin_filter_site)(request, order_manager)
    if not await order_manager.aexists():
        raise BusinessException("001")
    return await order_manager.afirst()


def _status_error(status: int):
    return BusinessException("002", {"status_name": OrderStatusChoices(status).label})


async def _apply_transition(order: Order, user, memo: str | None, action: str):
    def _do():
        sm = OrderStateMachine(order, user, memo)
        getattr(sm, action)()
        sm.save_state()
    await sync_to_async(_do, thread_sensitive=True)()


class CancelView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单取消失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单状态[{status_name}]无法进行该操作"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.OrderActionSchema = Body(..., description="订单取消")
    ):
        order = await _get_order_with_site_filter(request, data.order_id)
        if order.order_status not in [OrderStatusChoices.CREATED, OrderStatusChoices.CONFIRMED]:
            raise _status_error(order.order_status)

        await _apply_transition(order, request.user, data.operator_memo, "cancel")
        await sync_to_async(order_canceled_signal.send, thread_sensitive=True)(sender=Order, instance=order)


class ConfirmView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单确认失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单状态[{status_name}]无法进行该操作"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.OrderActionSchema = Body(..., description="订单确认")
    ):
        order = await _get_order_with_site_filter(request, data.order_id)
        if order.order_status != OrderStatusChoices.CREATED:
            raise _status_error(order.order_status)

        await _apply_transition(order, request.user, data.operator_memo, "confirm")


class ScheduleView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单排产失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单状态[{status_name}]无法进行该操作"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.OrderActionSchema = Body(..., description="订单排产")
    ):
        order = await _get_order_with_site_filter(request, data.order_id)
        if order.order_status != OrderStatusChoices.CONFIRMED:
            raise _status_error(order.order_status)

        await _apply_transition(order, request.user, data.operator_memo, "schedule")


class StartProductionView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单进入生产失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单状态[{status_name}]无法进行该操作"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.OrderActionSchema = Body(..., description="订单进入生产")
    ):
        order = await _get_order_with_site_filter(request, data.order_id)
        if order.order_status != OrderStatusChoices.SCHEDULED:
            raise _status_error(order.order_status)

        await _apply_transition(order, request.user, data.operator_memo, "start_production")


class FinishProductionView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单生产完成失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单状态[{status_name}]无法进行该操作"),
        ("003", "当前订单已绑定流程，请先完成流程后再生产完成"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.OrderActionSchema = Body(..., description="订单生产完成")
    ):
        order = await _get_order_with_site_filter(request, data.order_id)
        if order.order_status != OrderStatusChoices.PRODUCING:
            raise _status_error(order.order_status)

        sm = OrderStateMachine(order, request.user, data.operator_memo)
        allowed, _ = sm.can_finish_production()
        if not allowed:
            raise BusinessException("003")
        await _apply_transition(order, request.user, data.operator_memo, "finish_production")


class CompleteView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端订单签收完成失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单状态[{status_name}]无法进行该操作"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.OrderActionSchema = Body(..., description="订单签收完成")
    ):
        order = await _get_order_with_site_filter(request, data.order_id)
        if order.order_status != OrderStatusChoices.SHIPPED:
            raise _status_error(order.order_status)

        await _apply_transition(order, request.user, data.operator_memo, "complete")
        await sync_to_async(order_complete_signal.send, thread_sensitive=True)(sender=Order, instance=order)
