# -*-coding:utf-8 -*-

"""
# File       : site_filter_mixins.py
# Time       : 2025-11-10 13:47:50
# Author     : lyx
# version    : python 3.11
# Description: 站点过滤
"""
from site_mgmt.utils import admin_filter_site

class SiteFilterMixin:
    
    site_field_name = "site"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = admin_filter_site(request, queryset, self.site_field_name)
        return queryset