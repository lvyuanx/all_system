# -*-coding:utf-8 -*-

"""
# File       : mobile_profile_view.py
# Description: 移动端查询个人信息接口
"""

from core.conf import settings
from core.ninja_extra.api_extra import BaseApi, BusinessException, Warning, HttpRequest
from core.auth.models import User
from core.utils import token_util, auth_channel_util
from asgiref.sync import sync_to_async

from .schemas import MobileProfileSchema


SECRET_KEY = settings.SECRET_KEY


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["GET"]
    wrap_response = True
    response_schema = MobileProfileSchema
    error_codes = [
        ("001", Warning("未登录或 Token 无效")),
        ("002", Warning("用户不存在")),
    ]

    @staticmethod
    async def api(request: HttpRequest):
        channel_conf = auth_channel_util.get_channel_config("mobile")
        token = token_util.get_token_by_origins(request, channel_conf["token_tag"], channel_conf["read_from"])
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

        return MobileProfileSchema(
            uid=user.pk,
            username=user.username,
            first_name=user.first_name or None,
            last_name=user.last_name or None,
            full_name=getattr(user, "full_name", None),
            email=user.email or None,
            phone=getattr(user, "phone", None),
            sex=getattr(user, "sex", None),
            age=getattr(user, "age", None),
            avatar=user.avatar.url if getattr(user, "avatar", None) else None,
        )
