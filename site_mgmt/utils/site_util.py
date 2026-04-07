from asgiref.sync import sync_to_async
from django.http import HttpRequest
from django.db.models import QuerySet

from site_mgmt.models import SysSite
from staff.models import Staff


def admin_filter_site(
    request: HttpRequest, queryset: QuerySet, site_field_name: str = "site"
):
    user = request.user
    if not getattr(user, "is_authenticated", False):
        return queryset.none()
    if user.is_superuser:  # 超级管理员
        return queryset
    try:
        user_site = user.staff.site
    except Exception:
        return queryset.none()
    return queryset.filter(**{site_field_name: user_site})


def get_cur_sites(request: HttpRequest) -> QuerySet[SysSite]:
    """获取当前用户所在的站点（sync）"""
    user = request.user

    if user.is_superuser:
        return SysSite.objects.all()

    try:
        staff = Staff.objects.get(user=user)
    except Staff.DoesNotExist:
        return SysSite.objects.none()

    # staff.site may be FK (single site) or M2M manager
    site_attr = getattr(staff, "site", None)
    if site_attr is None:
        return SysSite.objects.none()
    if hasattr(site_attr, "all"):
        return site_attr.all()
    # FK: wrap single site into queryset
    return SysSite.objects.filter(pk=site_attr.pk)


async def aget_cur_sites(request: HttpRequest) -> list[SysSite]:
    """获取当前用户所在的站点"""
    return await sync_to_async(lambda: list(get_cur_sites(request)))()
