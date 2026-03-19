# -*-coding:utf-8 -*-
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from .mock_data import MOCK_STATUS


class DashboardStatusView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘状态分布失败"
    response_schema = list
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return MOCK_STATUS
