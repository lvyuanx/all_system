# -*-coding:utf-8 -*-

"""
# File       : pack_all_view.py
# Time       : 2025-08-13 11:01:55
# Author     : lyx
# version    : python 3.11
# Description: 查询所有权限包
"""

from typing import List
from core.ninja_extra.api_extra import BaseApi
from core.utils import perm_util
from ..schemas import PermPackItemSchema


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.ARCHIVED
    methods = ["GET"]
    finally_code = "000", "查询权限包失败"
    response_schema = List[PermPackItemSchema]

    @staticmethod
    async def api(request):
        perm_pack_dict = perm_util.merge_perm()
        packs: List[PermPackItemSchema] = []
        for key, value in perm_pack_dict.items():
            packs.append(PermPackItemSchema(
                pack_code=key,
                pack_name=value["name"]
            ))
        return packs