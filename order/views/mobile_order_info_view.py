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
from client_mgmt.models import Client
from site_mgmt.utils import site_util
from flow_engine.enums import FlowStatusChoices, TaskStatusChoices
from flow_engine.models import FlowTask

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
        cur_user = await common_util.get_user_async(request)
        perm_pack_codes = set(
            await sync_to_async(list)(
                cur_user.groups.filter(permission_packs__isnull=False)
                .values_list("permission_packs__pack_code", flat=True)
                .distinct()
            )
        )
        has_finance_perm = bool(cur_user.is_superuser) or bool(
            perm_pack_codes.intersection({"ORDER_CREATE_MANAGE", "FINANCE_MANAGE"})
        )
        has_logistics_perm = bool(cur_user.is_superuser) or bool(
            perm_pack_codes.intersection({"ORDER_COMPLETE_MANAGE", "ORDER_CREATE_MANAGE"})
        )

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
            "flow_definition_id",
            "flow_definition__name",
            "flow_instance_id",
            "flow_instance__status",
            "flow_instance__current_node__name",
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

        flow_summary = schemas.OrderFlowSummarySchema(
            has_workflow=bool(order_obj.get("flow_definition_id")),
            flow_definition_id=order_obj.get("flow_definition_id"),
            flow_definition_name=order_obj.get("flow_definition__name"),
            flow_instance_id=order_obj.get("flow_instance_id"),
            flow_status=order_obj.get("flow_instance__status"),
            current_node_name=order_obj.get("flow_instance__current_node__name"),
            auto_finish_on_done=bool(order_obj.get("flow_definition_id")),
        )
        if flow_summary.flow_status == FlowStatusChoices.RUNNING:
            flow_summary.flow_status_label = "进行中"
        elif flow_summary.flow_status == FlowStatusChoices.FINISHED:
            flow_summary.flow_status_label = "已完成"
        elif flow_summary.flow_status == FlowStatusChoices.REJECTED:
            flow_summary.flow_status_label = "已驳回"
        elif flow_summary.flow_status == FlowStatusChoices.CANCELED:
            flow_summary.flow_status_label = "已取消"

        if flow_summary.flow_instance_id:
            flow_summary.pending_task_count = await sync_to_async(
                lambda: FlowTask.objects.filter(
                    instance_id=flow_summary.flow_instance_id,
                    status=TaskStatusChoices.PENDING,
                ).count()
            )()

        production_action = schemas.OrderProductionActionSchema()
        if order_obj.get("order_status") == OrderStatusChoices.SCHEDULED:
            production_action.action = "start_production"
            production_action.enabled = True
            if flow_summary.has_workflow:
                production_action.label = "开始生产并进入流程"
                production_action.mode = "workflow"
                production_action.tips = "点击后订单会进入生产中，并自动发起生产流程。"
            else:
                production_action.label = "开始生产"
                production_action.mode = "manual"
                production_action.tips = "点击后订单进入生产中。"
        elif order_obj.get("order_status") == OrderStatusChoices.PRODUCING:
            if flow_summary.has_workflow:
                production_action.action = None
                production_action.label = "流程处理中"
                production_action.enabled = False
                production_action.mode = "workflow"
                production_action.tips = "流程结束后，系统会自动完成生产。"
            else:
                production_action.action = "finish_production"
                production_action.label = "生产完成"
                production_action.enabled = True
                production_action.mode = "manual"
                production_action.tips = "点击后订单进入已完工。"

        if flow_summary.has_workflow:
            if order_obj.get("order_status") == OrderStatusChoices.SCHEDULED:
                flow_summary.message = "开始生产后会自动进入流程，流程结束后自动完成生产。"
            elif order_obj.get("order_status") == OrderStatusChoices.PRODUCING:
                flow_summary.message = "当前订单正在走生产流程，流程结束后会自动完成生产。"
            elif flow_summary.flow_status == FlowStatusChoices.FINISHED:
                flow_summary.message = "生产流程已完成。"

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
            if not has_finance_perm:
                item["unit_price"] = Decimal("0")
                item["discount_price"] = Decimal("0")
                item["total"] = Decimal("0")
                item["subtotal"] = Decimal("0")
            items.append(item)

        if not has_finance_perm:
            order_obj["total_amount"] = Decimal("0")
            order_obj["discount_amount"] = Decimal("0")
            order_obj["shipping_fee"] = Decimal("0")
            order_obj["payable_amount"] = Decimal("0")
            order_obj["paid_amount"] = Decimal("0")
            order_obj["pay_status_str"] = ""

        if not has_logistics_perm:
            order_obj["ship_status_str"] = ""
            order_obj["tracking_no"] = None
            order_obj["shipping_party"] = None
            order_obj["shipping_party_company"] = None
            order_obj["shipping_party_phone"] = None
            order_obj["shipping_party_address"] = None
            order_obj["receiver_name"] = None
            order_obj["receiver_phone"] = None
            order_obj["receiver_company"] = None
            order_obj["receiver_address"] = None

        order_obj["items"] = items
        order_obj["flow_summary"] = flow_summary
        order_obj["production_action"] = production_action

        # 查询关联客户ID
        receiver_phone = order_obj.get("receiver_phone")
        receiver_client_id = None
        if receiver_phone:
            client = await Client.objects.filter(
                client_phone=receiver_phone, is_active=True
            ).values(client_id=F("pk")).afirst()
            if client:
                receiver_client_id = client["client_id"]
        order_obj["receiver_client_id"] = receiver_client_id

        return schemas.MobileOrderInfoSchema(**order_obj)
