# -*-coding:utf-8 -*-

"""
# File       : mobile_order_timeline_view.py
# Description: 移动端订单操作日志
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.utils import time_util
from order.enums import OrderStatusChoices
from order.models import Order, OrderCa
from site_mgmt.utils import site_util

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "移动端订单日志查询失败"
    response_schema = list[schemas.OrderTimelineItemSchema]
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
            "create_user__full_name",
            "create_user__phone",
            "create_time",
        ).afirst()

        timeline_lst = [
            {
                "item_title": "创建订单",
                "item_user": order_obj.get("create_user__full_name"),
                "item_phone": order_obj.get("create_user__phone"),
                "item_time": time_util.datetime_to_str(order_obj.get("create_time")),
                "item_memo": "",
            }
        ]

        ca_manager = OrderCa.objects.filter(order_id=order_id).order_by("id").values(
            "operator_name",
            "operator_phone",
            "operator_time",
            "operator_memo",
            "cur_status",
        )
        async for ca in ca_manager:
            timeline_lst.append(
                {
                    "item_title": OrderStatusChoices(ca["cur_status"]).label,
                    "item_user": ca["operator_name"],
                    "item_phone": ca["operator_phone"],
                    "item_time": time_util.datetime_to_str(ca["operator_time"]),
                    "item_memo": ca["operator_memo"],
                }
            )

        return timeline_lst
