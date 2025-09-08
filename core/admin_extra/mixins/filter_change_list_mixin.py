# -*-coding:utf-8 -*-

"""
# File       : filter_change_list_mixin.py
# Time       : 2025-09-08 10:38:00
# Author     : lyx
# version    : python 3.11
# Description: 记录url中的过滤条件，并且可以和页面中的过滤条件结合
"""

from django.contrib.admin.views.main import ChangeList
from django.urls import path
from django.db.models import Q


class FilteredChangeList(ChangeList):
    """
    通用 ChangeList，支持 /filter/ 路径下启用 get_filter_queryset
    并兼容 search_fields 搜索
    """

    def get_queryset(self, request):
        # 获取基础 queryset
        qs = super().get_queryset(request)

        # 只在 _filter URL 下启用自定义过滤
        if hasattr(self.model_admin, "get_filter_queryset") and getattr(
            request.resolver_match, "url_name", ""
        ).endswith("_filter"):
            # 自定义过滤
            qs = self.model_admin.get_filter_queryset(qs, request)

            # 兼容 search_fields
            search_query = request.GET.get('q', '').strip()
            if search_query and hasattr(self.model_admin, 'get_search_results'):
                qs, _ = self.model_admin.get_search_results(request, qs, search_query)

        return qs

    def get_results(self, request):
        """
        确保 full_result_count 使用过滤后的 queryset
        """
        super().get_results(request)
        if hasattr(self.model_admin, "get_filter_queryset") and getattr(
            request.resolver_match, "url_name", ""
        ).endswith("_filter"):
            qs = self.model_admin.get_filter_queryset(self.queryset.all(), request)

            # 兼容 search_fields
            search_query = request.GET.get('q', '').strip()
            if search_query and hasattr(self.model_admin, 'get_search_results'):
                qs, _ = self.model_admin.get_search_results(request, qs, search_query)

            self.full_result_count = qs.count()
            self.result_list = list(qs)


class FilterChangeListMixin:
    """
    通用 Mixin：支持 /filter/ URL 下启用过滤逻辑，并保留搜索条件
    """

    filter_url_name_suffix = "_filter"
    skip_filter_fields = []

    def get_filter_queryset(self, qs, request):
        """
        支持多参数、多值过滤，并跳过 q 搜索参数
        """
        skip_keys = set(getattr(self, "skip_filter_fields", [])) | {"q"}

        for key in request.GET.keys():
            if key in skip_keys:
                continue

            values = request.GET.getlist(key)
            if not values:
                continue

            if "__" in key and not key.endswith("__in"):
                # 多值用 Q 对象 OR 连接
                if len(values) == 1:
                    qs = qs.filter(**{key: values[0]})
                else:
                    q_obj = Q()
                    for v in values:
                        q_obj |= Q(**{key: v})
                    qs = qs.filter(q_obj)
            else:
                # 普通字段使用 __in
                if len(values) == 1:
                    qs = qs.filter(**{key: values[0]})
                else:
                    qs = qs.filter(**{f"{key}__in": values})

        # search_fields 逻辑
        search_query = request.GET.get('q', '').strip()
        if search_query and hasattr(self, 'get_search_results'):
            qs, _ = self.get_search_results(request, qs, search_query)

        return qs

    def get_changelist(self, request, **kwargs):
        return FilteredChangeList

    def get_urls(self):
        """
        增加 /filter/ 自定义 URL
        """
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            path(
                "filter/",
                self.admin_site.admin_view(self.changelist_view),
                name=f"{info[0]}_{info[1]}{self.filter_url_name_suffix}",
            )
        ]
        return custom_urls + urls

    # def changelist_view(self, request, extra_context=None):
    #     """
    #     方案B：保留 /filter/ URL 下的原有 GET 参数，
    #     搜索表单提交也会保留多参数过滤条件
    #     """
    #     return super().changelist_view(request, extra_context)
