from asgiref.sync import sync_to_async
from django.http import HttpRequest
from django.db.models import QuerySet

from site_mgmt.models import SysSite
from staff.models import Staff


def admin_filter_site(
    request: HttpRequest, queryset: QuerySet, site_field_name: str = "site"
):
    user = request.user
    if user.is_superuser:  # 超级管理员
        return queryset
    user_site = user.staff.site
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

    return staff.site.all()


async def aget_cur_sites(request: HttpRequest) -> list[SysSite]:
    """获取当前用户所在的站点"""
    return await sync_to_async(lambda: list(get_cur_sites(request)))()
