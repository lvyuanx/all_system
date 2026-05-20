# -*-coding:utf-8 -*-

"""
# File       : cur_site_options_view.py
# Time       : 2026-01-28 23:17:33
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询当前用户所在的站点
"""

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.common.schemas import ChoicesListItemSchema
from site_mgmt.utils import site_util

class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询当前用户所在的站点失败"
    response_schema = list[ChoicesListItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        sites = await site_util.aget_cur_sites(request)
        
        return [
            ChoicesListItemSchema(
                label=site.site_name,
                name=site.site_name,
                value=site.pk
            ) for site in sites
        ]
        
