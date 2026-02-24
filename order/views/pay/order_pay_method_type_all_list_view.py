# -*-coding:utf-8 -*-

"""
# File       : order_delivery_all_list.py
# Time       : 2026-01-22 21:16:16
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询所有订单支付类型
"""

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.common.schemas import ChoicesListItemSchema
from core.utils.common_util import choices_to_schema
from order import enums


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询所有订单支付类型失败"
    response_schema = list[ChoicesListItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return choices_to_schema(enums.OrderPayMehtodChoices)