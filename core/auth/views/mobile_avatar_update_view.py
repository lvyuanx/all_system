# -*-coding:utf-8 -*-

"""
# File       : mobile_avatar_update_view.py
# Description: 移动端修改用户头像接口
"""

from asgiref.sync import sync_to_async

from core.conf import settings
from core.ninja_extra.api_extra import BaseApi, BusinessException, Warning, HttpRequest
from core.auth.models import User
from core.utils import token_util, auth_channel_util


SECRET_KEY = settings.SECRET_KEY


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    response_schema = str
    methods = ["POST"]
    error_codes = [
        ("001", Warning("未登录或 Token 无效")),
        ("002", Warning("用户不存在")),
        ("003", Warning("请上传头像文件")),
        ("004", Warning("头像格式不支持，请上传 jpg/jpeg/png/gif 格式")),
    ]

    @staticmethod
    async def api(request: HttpRequest):
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

        avatar_file = request.FILES.get("avatar")
        if not avatar_file:
            raise BusinessException("003")

        allowed_types = {"image/jpeg", "image/png", "image/gif", "image/jpg"}
        if avatar_file.content_type not in allowed_types:
            raise BusinessException("004")

        def _save_avatar():
            if user.avatar and user.avatar.name != settings.DEFAULT_AVATAR:
                user.avatar.delete(save=False)
            user.avatar.save(avatar_file.name, avatar_file, save=True)

        await sync_to_async(_save_avatar)()

        avatar_url = user.avatar.url if user.avatar else None
        return avatar_url
