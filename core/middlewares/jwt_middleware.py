# -*-coding:utf-8 -*-

"""
# File       : jwt_middleware.py
# Time       : 2025-07-27 23:09:53
# Author     : lyx
# version    : python 3.11
# Description: jwt校验中间件
"""
import logging
from django.http import HttpRequest, HttpResponse, JsonResponse
from jwt import ExpiredSignatureError
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

from core.utils import token_util
from core.conf import settings
from core.ninja_extra.response_schema import ErrorResponse, ResponseLevel

logger = logging.getLogger(__name__)

TOKEN_ORIGIN = settings.TOKEN_ORIGIN  # token来源
TOKEN_TAG = settings.TOKEN_TAG  # token标记名称
SECRET_KEY = settings.SECRET_KEY
TOKEN_EXPIRE = settings.TOKEN_EXPIRE  # token过期时间
token_handler = token_util.tk_handler_dict[TOKEN_ORIGIN]
NINJA_BASE_URL = settings.NINJA_BASE_URL

class JWTMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        
    def __call__(self, request: HttpRequest):

        req_paht = request.path
        if req_paht.startswith("/admin/login/"):
            return self.get_response(request)

        is_admin = req_paht.startswith("/admin/")
        token = token_handler.get(request, TOKEN_TAG)  # 去指定来源获取token
        if not token and hasattr(request, "new_token"):
            token = request.new_token  # token 可能是上层拦截器生成的
            
        if not token:
            if is_admin:
                # 先退出登录
                if request.user.is_authenticated:
                    logout(request)
                    return redirect(reverse("admin:login"))  # 跳转登录页
            else:
                return JsonResponse(
                    ErrorResponse(
                        code="401", 
                        msg="未登录",
                        level=ResponseLevel.ERROR
                    ).model_dump(), 
                    status=200
                )
        
        try:
            token  = token_util.verify_token(token, SECRET_KEY)
        except ExpiredSignatureError:
            logger.warning(f'token已过期 - {token}')
            if is_admin:
                # 先退出登录
                if request.user.is_authenticated:
                    logout(request)
                    return redirect(reverse("admin:login"))  # 跳转登录页
            else:
                return JsonResponse(
                    ErrorResponse(
                        code="401", 
                        msg="未登录",
                        level=ResponseLevel.ERROR
                    ).model_dump(), 
                    status=200
                )
        except Exception:
            logger.error(f'token验证失败 - {token}', exc_info=True)
            if is_admin:
                # 先退出登录
                if request.user.is_authenticated:
                    logout(request)
                    return redirect(reverse("admin:login"))  # 跳转登录页
            else:
                return JsonResponse(
                    ErrorResponse(
                        code="404", 
                        msg="未登录",
                        level=ResponseLevel.ERROR
                    ).model_dump(), 
                    status=200
                )
    
        return self.get_response(request)

