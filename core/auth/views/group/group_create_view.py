# -*-coding:utf-8 -*-

"""
# File       : group_create_view.py
# Time       : 2025-08-13 11:36:51
# Author     : lyx
# version    : python 3.11
# Description: 根据权限包创建角色
"""
from asgiref.sync import sync_to_async
from typing import List
from django.http import Http404
from django.db import transaction, models
from django.contrib.auth.models import Group
from core.ninja_extra.api_extra import BaseApi, Body, BusinessException, Warning, HttpRequest
from core.utils import perm_util
from ..schemas import GroupCreateSchema
from ...models import PermissionPack
from core.utils import admin_util


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.ARCHIVED
    methods = ["POST"]
    finally_code = "000", "角色创建失败"
    error_codes = [
        ("001", Warning("请最少选择一个权限")),
        ("002", "权限[{perm_name}]不存在，请联系管理员！"),
        ("003", Warning("角色[{group_name}]已存在，请勿重复创建！")),
    ]

    
    @staticmethod
    @transaction.atomic()
    def transaction_func(request: HttpRequest, pack_queryset: models.Manager[PermissionPack], group_name: str):
        # 创建角色
        group_obj = Group.objects.create(name=group_name)
        
        # 给权限包绑定角色
        pack_objs = [pack for pack in pack_queryset]
        for pack in pack_objs:
            pack.add_group(group_obj)
        
        admin_util.log_custom_action(request, group_obj, f"创建角色[{group_name}]")
    
    @staticmethod
    async def api(request: HttpRequest, group: GroupCreateSchema = Body(..., description="角色信息")):
        packs = group.packs
        if not packs:
            raise BusinessException("001")
        
        # 校验角色是否存在
        group_name = group.name
        if await Group.objects.filter(name=group_name).aexists():
            raise BusinessException("003", {"group_name": group_name})
        
        # 校验权限包是否存在
        pack_queryset = PermissionPack.objects.filter(pack_code__in=packs)
        if await pack_queryset.acount() != len(packs):
            pack_codes = pack_queryset.values_list("pack_code", flat=True)
            pack_codes = [pack_code async for pack_code in pack_codes]
            noexists = [pack for pack in packs if pack not in pack_codes]
            raise BusinessException("002", {"perm_name": ",".join(noexists)})
        
        await sync_to_async(View.transaction_func)(request, pack_queryset, group_name)
        
        
        
        
