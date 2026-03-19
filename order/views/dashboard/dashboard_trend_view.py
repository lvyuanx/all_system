# -*-coding:utf-8 -*-
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from .mock_data import MOCK_TREND


class DashboardTrendView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘趋势失败"
    response_schema = dict
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        # 可接受 range 参数，但当前返回完整数据，前端自行选择
        return MOCK_TREND
