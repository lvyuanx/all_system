# -*-coding:utf-8 -*-

"""
# File       : simpleui_menus_middleware.py
# Time       : 2025-08-06 22:21:15
# Author     : lyx
# version    : python 3.11
# Description: simpleui菜单中间件
"""
import logging
from django.http import HttpRequest, HttpResponse, Http404
from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from jwt import ExpiredSignatureError

from core.utils import simpleui_util

logger = logging.getLogger(__name__)


class SiteMiddlware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        
    def __call__(self, request: HttpRequest):

        if request.path == "/admin/":

            if hasattr(request, "user"):
                user = request.user
                if isinstance(user, AbstractBaseUser):
                    if user.is_superuser:  # 超级管理员
                        admin.site.site_header = "超管模式"
                        admin.site.site_title = "超管模式"
                        admin.site.index_title = "超管模式"
                        settings.SIMPLEUI_LOGO = "/static/images/default/superuser.png"
                    elif user.staff:
                        user_site = user.staff.site
                        admin.site.site_header = user_site.site_name
                        admin.site.site_title = user_site.site_name
                        admin.site.index_title = "3"
                        site_logo = user_site.site_logo
                        if site_logo:
                            settings.SIMPLEUI_LOGO = f"{settings.MEDIA_URL}{site_logo}"
                    else:
                        admin.site.site_header = "游客模式"
                        admin.site.site_title = "游客模式"
                        admin.site.index_title = "游客模式"
                        settings.SIMPLEUI_LOGO = "/static/images/default/guestuser.png"
        return self.get_response(request)