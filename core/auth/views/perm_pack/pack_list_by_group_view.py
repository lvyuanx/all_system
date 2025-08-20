# -*-coding:utf-8 -*-

"""
# File       : pack_list_by_group_view.py
# Time       : 2025-08-13 22:13:26
# Author     : lyx
# version    : python 3.11
# Description: 根据角色查询权限包
"""
from typing import List
from django.contrib.auth.models import Group
from core.ninja_extra.api_extra import BaseApi, Query, Warning, BusinessException
from core.utils import perm_util
from ..schemas import PermPackItemSchema


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.ARCHIVED
    methods = ["GET"]
    finally_code = "000", "查询权限包失败"
    response_schema = List[PermPackItemSchema]
    error_codes = [
        ("001", "角色[{gid}]不存在"),
    ]

    @staticmethod
    async def api(request, gid: int = Query(..., description="角色id")):
        group_manager = Group.objects.filter(id=gid)
        if not await group_manager.aexists():
            raise BaseException("001", {"gid": gid})
        
        group = await group_manager.afirst()
        packs = group.permission_packs.all().values("pack_code", "pack_name")
        return [
            PermPackItemSchema(pack_code=pack["pack_code"], pack_name=pack["pack_name"]) async for pack in packs
        ]
