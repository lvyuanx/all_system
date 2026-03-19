# -*-coding:utf-8 -*-
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from .mock_data import MOCK_PENDING_SHIP


class DashboardPendingShipView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询待发货订单失败"
    response_schema = list
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return MOCK_PENDING_SHIP
