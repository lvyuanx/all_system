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
from core.utils import common_util
from site_mgmt.models import SysSite
from staff.models import Staff

class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询当前用户所在的站点失败"
    response_schema = list[ChoicesListItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        user = await common_util.get_user_async(request)
        if user.is_superuser:
            sites = SysSite.objects.all()
        else:
            staff = await Staff.objects.aget(user=user)
            sites = staff.site.all()
        
        return [
            ChoicesListItemSchema(
                label=site.site_name,
                name=site.site_name,
                value=site.pk
            ) async for site in sites
        ]
        