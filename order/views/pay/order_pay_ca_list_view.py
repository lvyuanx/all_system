# -*-coding:utf-8 -*-

"""
# File       : order_pay_ca_list_view.py
# Time       : 2026-02-24 21:06:12
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询订单支付流水
"""

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.utils import time_util
from order.enums import OrderPayMehtodChoices
from order.models import Order, OrderPayCa
from .. import schemas


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询订单支付流水失败"
    response_schema = list[schemas.OrderPayCaListItemSchema]
    error_codes = [
        ("001", "订单不存在")
    ]

    @staticmethod
    async def api(request: HttpRequest, oid: int = Query(..., description="订单ID")):
        if not await Order.objects.filter(pk=oid, is_delete=False).aexists():
            raise BusinessException("001")
        
        lst = OrderPayCa.objects.filter(order_id=oid).values(
            "ca_no", "pay_amount", "pay_method",  "operator_name", "operator_phone", "operator_time", "operator_memo"
        )

        async for item in lst:
            item["pay_method_str"] = OrderPayMehtodChoices(item["pay_method"]).label
            item["operator_time_str"] = time_util.datetime_to_str(item["operator_time"])
            item["operator_info"] = f"{item['operator_name']}({item['operator_phone']})"

        return lst
