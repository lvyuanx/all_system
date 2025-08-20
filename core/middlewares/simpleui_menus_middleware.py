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
from django.contrib.auth.models import AbstractBaseUser
from jwt import ExpiredSignatureError

from core.utils import simpleui_util
from core.conf import settings

logger = logging.getLogger(__name__)


class SimpleuiMenusMiddlware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        
    def __call__(self, request: HttpRequest):

        if request.path == "/admin/":

            if hasattr(request, "user") and isinstance(request.user, AbstractBaseUser):
                menus = simpleui_util.get_dynamic_menus(request)
                settings.SIMPLEUI_CONFIG["menus"] = menus
        
        return self.get_response(request)