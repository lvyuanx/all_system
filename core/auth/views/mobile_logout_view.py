# -*-coding:utf-8 -*-

"""
# File       : mobile_logout_view.py
# Description: 移动端退出登录接口
"""

from asgiref.sync import sync_to_async
from django.contrib.auth import logout
from django.http import JsonResponse

from core.conf import settings
from core.ninja_extra.api_extra import BaseApi, BusinessException, Warning, HttpRequest
from core.ninja_extra.response_schema import SuccessResponse
from core.utils import token_util, auth_channel_util


SECRET_KEY = settings.SECRET_KEY


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    wrap_response = False
    finally_code = "000", "退出登录失败"
    error_codes = [
        ("001", Warning("未登录或 Token 无效")),
    ]

    @staticmethod
    async def api(request: HttpRequest):
        channel_conf = auth_channel_util.get_channel_config("mobile")
        token_tag = channel_conf["token_tag"]
        token_read_from = channel_conf["read_from"]
        token_write_to = channel_conf["write_to"]

        token = token_util.get_token_by_origins(request, token_tag, token_read_from)
        if not token:
            raise BusinessException("001")

        try:
            token_util.verify_token(token, SECRET_KEY)
        except Exception:
            raise BusinessException("001")

        await sync_to_async(logout)(request)

        response_data = SuccessResponse(msg="退出登录成功").model_dump()
        response = JsonResponse(response_data, status=200)
        token_util.remove_token_by_origins(response, token_tag, token_write_to)
        return response
