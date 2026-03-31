# -*-coding:utf-8 -*-

"""
# File       : mobile_menu_view.py
# Description: 移动端菜单查询接口
"""

from asgiref.sync import sync_to_async
from django.db.models import Exists, OuterRef

from core.ninja_extra.api_extra import BaseApi, Query, HttpRequest, BusinessException, Warning
from core.auth.models import MobileMenus

from .schemas import MobileMenuItemSchema


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["GET"]
    wrap_response = True
    response_schema = list[MobileMenuItemSchema]
    error_codes = [
        ("001", Warning("父菜单不存在")),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        parent_id: int | None = Query(default=None, description="父菜单ID，不传则查询顶级菜单"),
    ):
        if parent_id is not None:
            parent = await sync_to_async(
                MobileMenus.objects.filter(id=parent_id, is_active=True).first
            )()
            if parent is None:
                raise BusinessException("001")
            parent_path = parent.path or str(parent.id)
            child_depath = parent.depath + 1

            menus = await sync_to_async(list)(
                MobileMenus.objects.filter(
                    is_active=True,
                    depath=child_depath,
                    path__startswith=parent_path + "/",
                ).order_by("sort_no", "id")
            )
        else:
            menus = await sync_to_async(list)(
                MobileMenus.objects.filter(
                    is_active=True,
                    depath=0,
                ).order_by("sort_no", "id")
            )

        # 判断每个菜单是否有子菜单
        result = []
        for menu in menus:
            menu_path = menu.path or str(menu.id)
            has_children = await sync_to_async(
                MobileMenus.objects.filter(
                    is_active=True,
                    depath=menu.depath + 1,
                    path__startswith=menu_path + "/",
                ).exists
            )()
            result.append(MobileMenuItemSchema(
                id=menu.id,
                name=menu.name,
                icon=menu.icon,
                url=menu.url,
                path=menu.path,
                depath=menu.depath,
                sort_no=menu.sort_no or 0,
                has_children=has_children,
            ))

        return result
