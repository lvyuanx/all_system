# -*-coding:utf-8 -*-

"""
# File       : mobile_change_password_view.py
# Description: 移动端修改密码接口（修改后退出登录）
"""

from asgiref.sync import sync_to_async
from django.contrib.auth import logout
from django.http import JsonResponse

from core.conf import settings
from core.ninja_extra.api_extra import BaseApi, Body, BusinessException, Warning, HttpRequest
from core.ninja_extra.response_schema import SuccessResponse
from core.auth.models import User
from core.utils import token_util, auth_channel_util

from .schemas import MobileChangePasswordSchema


SECRET_KEY = settings.SECRET_KEY


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    wrap_response = False
    error_codes = [
        ("001", Warning("未登录或 Token 无效")),
        ("002", Warning("用户不存在")),
        ("003", Warning("旧密码错误")),
        ("004", Warning("新密码不能与旧密码相同")),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        params: MobileChangePasswordSchema = Body(..., description="修改密码参数"),
    ):
        channel_conf = auth_channel_util.get_channel_config("mobile")
        token_tag = channel_conf["token_tag"]
        token_read_from = channel_conf["read_from"]
        token_write_to = channel_conf["write_to"]

        token = token_util.get_token_by_origins(request, token_tag, token_read_from)
        if not token:
            raise BusinessException("001")

        try:
            payload = token_util.verify_token(token, SECRET_KEY)
        except Exception:
            raise BusinessException("001")

        uid = payload.get("uid")
        user: User = await sync_to_async(User.objects.filter(pk=uid).first)()
        if user is None:
            raise BusinessException("002")

        valid = await sync_to_async(user.check_password)(params.old_password)
        if not valid:
            raise BusinessException("003")

        if params.old_password == params.new_password:
            raise BusinessException("004")

        await sync_to_async(user.set_password)(params.new_password)
        await sync_to_async(user.save)()
        await sync_to_async(logout)(request)

        response = JsonResponse(
            SuccessResponse(msg="密码修改成功，请重新登录").model_dump(),
            status=200,
        )
        token_util.remove_token_by_origins(response, token_tag, token_write_to)
        return response
