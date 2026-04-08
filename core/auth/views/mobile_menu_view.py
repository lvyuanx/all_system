# -*-coding:utf-8 -*-

"""
# File       : mobile_menu_view.py
# Description: 移动端菜单查询接口
"""

from asgiref.sync import sync_to_async

from core.ninja_extra.api_extra import BaseApi, Query, HttpRequest, BusinessException, Warning
from core.auth.models import MobileMenus
from core.utils import common_util

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
    def _has_permission(menu: MobileMenus, is_superuser: bool, user_permissions: set[str]) -> bool:
        if is_superuser:
            return True

        perms = list(menu.permissions.all())
        if not perms:
            return True

        for perm in perms:
            perm_str = f"{perm.content_type.app_label}.{perm.codename}"
            if perm_str in user_permissions:
                return True
        return False

    @staticmethod
    async def api(
        request: HttpRequest,
        parent_id: int | None = Query(default=None, description="父菜单ID，不传则查询顶级菜单"),
    ):
        cur_user = await common_util.get_user_async(request)
        is_superuser = bool(cur_user.is_superuser)
        user_permissions = set(
            await sync_to_async(cur_user.get_all_permissions, thread_sensitive=True)()
        )

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
                )
                .prefetch_related("permissions__content_type")
                .order_by("sort_no", "id")
            )
        else:
            menus = await sync_to_async(list)(
                MobileMenus.objects.filter(
                    is_active=True,
                    depath=0,
                )
                .prefetch_related("permissions__content_type")
                .order_by("sort_no", "id")
            )

        visible_menus: list[MobileMenus] = []
        for menu in menus:
            if View._has_permission(menu, is_superuser, user_permissions):
                visible_menus.append(menu)
                continue
            # 顶层菜单兜底：如果其子菜单可见，则保留该顶层菜单
            if menu.depath == 0:
                menu_path = menu.path or str(menu.id)
                child_menus = await sync_to_async(list)(
                    MobileMenus.objects.filter(
                        is_active=True,
                        depath=menu.depath + 1,
                        path__startswith=menu_path + "/",
                    )
                    .prefetch_related("permissions__content_type")
                    .order_by("sort_no", "id")
                )
                if any(
                    View._has_permission(child, is_superuser, user_permissions)
                    for child in child_menus
                ):
                    visible_menus.append(menu)

        # 判断每个可见菜单是否有可见子菜单
        result = []
        for menu in visible_menus:
            menu_path = menu.path or str(menu.id)
            child_menus = await sync_to_async(list)(
                MobileMenus.objects.filter(
                    is_active=True,
                    depath=menu.depath + 1,
                    path__startswith=menu_path + "/",
                )
                .prefetch_related("permissions__content_type")
                .order_by("sort_no", "id")
            )
            has_children = any(
                View._has_permission(child, is_superuser, user_permissions)
                for child in child_menus
            )
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
