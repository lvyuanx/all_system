# -*-coding:utf-8 -*-

"""
# File       : mobile_profile_update_view.py
# Description: 移动端修改个人信息接口（修改后退出登录）
"""

from asgiref.sync import sync_to_async
from django.contrib.auth import logout

from core.conf import settings
from core.ninja_extra.api_extra import BaseApi, Body, BusinessException, Warning, HttpRequest
from core.auth.models import User
from core.utils import token_util, auth_channel_util

from .schemas import MobileProfileUpdateSchema


SECRET_KEY = settings.SECRET_KEY

UPDATABLE_FIELDS = ("username", "first_name", "last_name", "email", "phone", "sex", "age")


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    response_schema = None
    methods = ["POST"]
    error_codes = [
        ("001", Warning("未登录或 Token 无效")),
        ("002", Warning("用户不存在")),
        ("003", Warning("用户名已被占用")),
        ("004", Warning("手机号已被占用")),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        params: MobileProfileUpdateSchema = Body(..., description="修改参数"),
    ):
        channel_conf = auth_channel_util.get_channel_config("mobile")
        token_tag = channel_conf["token_tag"]
        token_read_from = channel_conf["read_from"]

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

        update_data = params.model_dump(exclude_none=True)

        if "username" in update_data:
            conflict = await sync_to_async(
                User.objects.filter(username=update_data["username"]).exclude(pk=uid).exists
            )()
            if conflict:
                raise BusinessException("003")

        if "phone" in update_data:
            conflict = await sync_to_async(
                User.objects.filter(phone=update_data["phone"]).exclude(pk=uid).exists
            )()
            if conflict:
                raise BusinessException("004")

        for field in UPDATABLE_FIELDS:
            if field in update_data:
                setattr(user, field, update_data[field])

        await sync_to_async(user.save)()
        await sync_to_async(logout)(request)
