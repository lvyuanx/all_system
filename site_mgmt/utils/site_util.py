

from django.http import HttpRequest
from django.db.models import QuerySet


def admin_filter_site(request: HttpRequest, queryset: QuerySet, site_field_name: str = "site"):
    user = request.user
    if user.is_superuser:  # 超级管理员
        return queryset
    user_site = user.staff.site
    return queryset.filter(**{site_field_name: user_site})
