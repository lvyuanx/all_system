# -*-coding:utf-8 -*-

"""
# File       : admin_login_to_jwt_middleware.py
# Time       : 2025-08-13 01:10:15
# Author     : lyx
# version    : python 3.11
# Description: admin 登录转jwt中间件
"""
import logging
from django.http import HttpRequest

from core.utils import token_util, auth_channel_util
from core.conf import settings

logger = logging.getLogger(__name__)
SECRET_KEY = settings.SECRET_KEY
TOKEN_EXPIRE = settings.TOKEN_EXPIRE  # token过期时间
ADMIN_CHANNEL_CONF = auth_channel_util.get_channel_config("admin")

class AdminLoginToJwtMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        user = request.user
        if user.is_authenticated and user.is_staff and getattr(request, 'admin_login_success', False):  # 登录用户且是后台工作人员
            token = token_util.create_token(
                payload={
                    "uid": user.pk,
                    "client": "admin",
                },
                secret=SECRET_KEY,
                expire_seconds=TOKEN_EXPIRE
            ) # 生成token
            token_util.set_token_by_origins(
                response=response,
                token_name=ADMIN_CHANNEL_CONF["token_tag"],
                token=token,
                origins=ADMIN_CHANNEL_CONF["write_to"],
            )
        return response
