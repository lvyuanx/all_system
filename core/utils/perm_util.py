# -*-coding:utf-8 -*-

"""
# File       : perm_util.py
# Time       : 2025-08-12 11:33:46
# Author     : lyx
# version    : python 3.11
# Description: 权限工具
"""
from django.db import transaction
from django.apps import apps

from core.conf import settings
from core.auth.models import PermissionPack
from core.utils.model_util import PermissionHelperMixin, PermWrapper

def merge_perm():
    """
    合并权限包配置
    """
    default_perm_packs = settings._PERM_PAKC
    perm_packs = settings.PERM_PAKC
    return {
        **default_perm_packs,
        **perm_packs
    }


@transaction.atomic
def init_perm():
    """初始化权限包"""
    merge_perm_dict = merge_perm()
    del_packs = PermissionPack.objects.exclude(pack_code__in=merge_perm_dict.keys())
    if del_packs.exists():
        for pack in del_packs:
            pack.remove_groups()
            pack.remove_permissions()
            pack.delete()
    
    for perm_pack_code, perm_pack_data in merge_perm().items():
        perm_pack_name = perm_pack_data["name"]

        groups = None # 权限包分配的权限组
        # region ******************** 如果权限包存在先删除,否则就创建 start ******************** #
        pack_manager = PermissionPack.objects.filter(pack_code=perm_pack_code)
        if pack_manager.exists():
            permission_pack = pack_manager.first()
            permission_pack.remove_groups()  # 删除权限包下的权限组
            permission_pack.remove_permissions()  # 删除权限包下的权限
        else:
            permission_pack = PermissionPack.objects.create(pack_name=perm_pack_name, pack_code=perm_pack_code)
        # endregion ****************** 如果权限包存在先删除,否则就创建 end ********************* #

        
        # region ******************** 重新创建权限包 start ******************** #
        for model_label, perms in perm_pack_data.get("models", {}).items():
            app_label, model_name = model_label.split(".")
            model_cls = apps.get_model(app_label, model_name)
            if issubclass(model_cls, PermissionHelperMixin):
                perm_objs = model_cls.get_perm_objs(perms)
                permission_pack.permissions.add(*perm_objs)
            else:
                for prem in perms:
                    perm_wrapper = PermWrapper(model_cls=model_cls, perm_type=prem)
                    permission_pack.permissions.add(perm_wrapper.prem)
        # endregion ****************** 重新创建权限包 end ********************* #

        # region ******************** 将权限包赋值给原来的组 start ******************** #
        if groups:
            permission_pack.add_group(*groups)
        # endregion ****************** 将权限包赋值给原来的组 end ********************* #


        
    