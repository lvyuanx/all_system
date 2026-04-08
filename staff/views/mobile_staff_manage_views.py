# -*-coding:utf-8 -*-

"""
# File       : mobile_staff_manage_views.py
# Description: 移动端员工管理（列表/详情/启用禁用/改权限组）
"""

from asgiref.sync import sync_to_async
from django.contrib.auth.models import Group
from django.db.models import F, Q, QuerySet
from ninja import Body, Query

from core.ninja_extra.api_extra import BaseApi, HttpRequest, BusinessException
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.auth.models import User
from core.utils import common_util
from site_mgmt.utils import site_util
from staff.models import Staff

from . import schemas


def _has_staff_manage_perm(user: User) -> bool:
    if user.is_superuser:
        return True
    return user.groups.filter(permission_packs__pack_code="STAFF_MANAGE").exists()


async def _ensure_staff_manage_perm(request: HttpRequest):
    cur_user = await common_util.get_user_async(request)
    has_perm = await sync_to_async(_has_staff_manage_perm)(cur_user)
    if not has_perm:
        raise BusinessException("403")
    return cur_user


async def _get_staff_queryset_by_scope(request: HttpRequest) -> QuerySet:
    qs = Staff.objects.select_related("user", "site")
    return await sync_to_async(site_util.admin_filter_site)(request, qs, "site")


class StaffListPagination(AsyncLimitOffsetPagination):
    InputSource = Body

    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        if not input_filter:
            return queryset

        search = (input_filter.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(staff_code__contains=search)
                | Q(user__full_name__contains=search)
                | Q(user__phone__contains=search)
                | Q(user__username__contains=search)
            )

        is_active = input_filter.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(user__is_active=bool(is_active))

        group_id = input_filter.get("group_id")
        if group_id:
            queryset = queryset.filter(user__groups__id=group_id)

        site_id = input_filter.get("site_id")
        if site_id:
            queryset = queryset.filter(site_id=site_id)

        return queryset

    async def aprocess_result(self, results: list) -> list:
        user_ids = [item["user_id"] for item in results if item.get("user_id")]
        group_map: dict[int, list[str]] = {}
        if user_ids:
            group_rows = await sync_to_async(list)(
                User.objects.filter(pk__in=user_ids)
                .values("id", "groups__name")
                .order_by("id")
            )
            for row in group_rows:
                uid = row.get("id")
                gname = row.get("groups__name")
                if not uid or not gname:
                    continue
                group_map.setdefault(uid, [])
                if gname not in group_map[uid]:
                    group_map[uid].append(gname)

        data = []
        for item in results:
            data.append(
                {
                    "staff_id": item.get("staff_id"),
                    "user_id": item.get("user_id"),
                    "staff_code": item.get("staff_code"),
                    "full_name": item.get("full_name"),
                    "username": item.get("username"),
                    "phone": item.get("phone"),
                    "avatar": common_util.media_url(item.get("avatar", "")),
                    "is_active": bool(item.get("is_active")),
                    "site_name": item.get("site_name"),
                    "group_names": group_map.get(item.get("user_id"), []),
                }
            )
        return data


class StaffListView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端查询员工列表失败"
    response_schema = schemas.MobileStaffListItemSchema
    is_pagination = True
    pagination_class = StaffListPagination
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        await _ensure_staff_manage_perm(request)
        qs = await _get_staff_queryset_by_scope(request)
        return qs.distinct().values(
            "staff_code",
            "user_id",
            full_name=F("user__full_name"),
            username=F("user__username"),
            phone=F("user__phone"),
            avatar=F("user__avatar"),
            is_active=F("user__is_active"),
            site_name=F("site__site_name"),
            staff_id=F("pk"),
        ).order_by("-id")


class StaffDetailView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "移动端查询员工详情失败"
    response_schema = schemas.MobileStaffDetailSchema
    error_codes = [
        ("001", "员工不存在"),
    ]

    @staticmethod
    async def api(request: HttpRequest, user_id: int = Query(..., description="用户ID")):
        await _ensure_staff_manage_perm(request)
        qs = await _get_staff_queryset_by_scope(request)
        staff = await qs.filter(user_id=user_id).values(
            "staff_code",
            "site_id",
            "user_id",
            site_name=F("site__site_name"),
            staff_id=F("pk"),
            full_name=F("user__full_name"),
            username=F("user__username"),
            first_name=F("user__first_name"),
            last_name=F("user__last_name"),
            email=F("user__email"),
            phone=F("user__phone"),
            sex=F("user__sex"),
            age=F("user__age"),
            avatar=F("user__avatar"),
            is_active=F("user__is_active"),
        ).afirst()
        if not staff:
            raise BusinessException("001")

        group_rows = await sync_to_async(list)(
            Group.objects.filter(user=user_id).values("id", "name")
        )
        group_ids = [g["id"] for g in group_rows]
        group_names = [g["name"] for g in group_rows]

        return schemas.MobileStaffDetailSchema(
            staff_id=staff["staff_id"],
            user_id=staff["user_id"],
            staff_code=staff["staff_code"],
            full_name=staff.get("full_name"),
            username=staff.get("username") or "",
            first_name=staff.get("first_name"),
            last_name=staff.get("last_name"),
            email=staff.get("email"),
            phone=staff.get("phone"),
            sex=staff.get("sex"),
            age=staff.get("age"),
            avatar=common_util.media_url(staff.get("avatar", "")),
            is_active=bool(staff.get("is_active")),
            site_id=staff.get("site_id"),
            site_name=staff.get("site_name"),
            group_ids=group_ids,
            group_names=group_names,
        )


class StaffActivateView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端启用员工账号失败"
    response_schema = None
    error_codes = [
        ("001", "员工不存在"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        data: schemas.MobileStaffStatusChangeSchema = Body(..., description="启用员工账号"),
    ):
        await _ensure_staff_manage_perm(request)
        qs = await _get_staff_queryset_by_scope(request)
        staff = await qs.filter(user_id=data.user_id).select_related("user").afirst()
        if not staff:
            raise BusinessException("001")
        staff.user.is_active = True
        await sync_to_async(staff.user.save)(update_fields=["is_active"])


class StaffDeactivateView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端禁用员工账号失败"
    response_schema = None
    error_codes = [
        ("001", "员工不存在"),
        ("002", "不能禁用当前登录账号"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        data: schemas.MobileStaffStatusChangeSchema = Body(..., description="禁用员工账号"),
    ):
        cur_user = await _ensure_staff_manage_perm(request)
        if int(cur_user.pk) == int(data.user_id):
            raise BusinessException("002")
        qs = await _get_staff_queryset_by_scope(request)
        staff = await qs.filter(user_id=data.user_id).select_related("user").afirst()
        if not staff:
            raise BusinessException("001")
        staff.user.is_active = False
        await sync_to_async(staff.user.save)(update_fields=["is_active"])


class StaffUpdateGroupsView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端修改员工权限组失败"
    response_schema = None
    error_codes = [
        ("001", "员工不存在"),
        ("002", "权限组不存在"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        data: schemas.MobileStaffUpdateGroupsSchema = Body(..., description="修改员工权限组"),
    ):
        await _ensure_staff_manage_perm(request)
        qs = await _get_staff_queryset_by_scope(request)
        staff = await qs.filter(user_id=data.user_id).select_related("user").afirst()
        if not staff:
            raise BusinessException("001")

        group_ids = list({int(i) for i in (data.group_ids or [])})
        groups = await sync_to_async(list)(Group.objects.filter(id__in=group_ids))
        if len(groups) != len(group_ids):
            raise BusinessException("002")
        await sync_to_async(staff.user.groups.set)(groups)


class StaffGroupOptionsView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "移动端查询权限组失败"
    response_schema = list[schemas.MobileGroupOptionSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        await _ensure_staff_manage_perm(request)
        groups = Group.objects.all().order_by("name").values("id", "name")
        return [
            schemas.MobileGroupOptionSchema(group_id=row["id"], group_name=row["name"])
            async for row in groups
        ]
