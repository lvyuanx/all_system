# -*-coding:utf-8 -*-

"""
# File       : get_province_view.py
# Time       : 2025-10-17 15:42:08
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 获取省
"""

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from ..models import ProvinceCode
from . import schemas



class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "获取省失败"
    response_schema = schemas.AddressLevelItemSchema
    error_codes = []
    is_pagination: bool = True

    @staticmethod
    async def api(request: HttpRequest):
        return ProvinceCode.objects.all().values("id", "code", "name")