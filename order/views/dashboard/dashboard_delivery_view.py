# -*-coding:utf-8 -*-
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from .mock_data import MOCK_DELIVERY


class DashboardDeliveryView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘配送方式失败"
    response_schema = list
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return MOCK_DELIVERY
