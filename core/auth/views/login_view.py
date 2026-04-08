# -*-coding:utf-8 -*-

"""
# File       : login_view.py
# Description: 登录接口
"""

from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate, login
from django.http import JsonResponse

from core.conf import settings
from core.ninja_extra.api_extra import BaseApi, Body, BusinessException, Warning, HttpRequest
from core.ninja_extra.response_schema import SuccessResponse
from core.utils import token_util, auth_channel_util

from .schemas import LoginRequestSchema, LoginResponseSchema


SECRET_KEY = settings.SECRET_KEY
TOKEN_EXPIRE = settings.TOKEN_EXPIRE


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    wrap_response = False
    finally_code = "000", "登录失败"
    error_codes = [
        ("001", Warning("账号和密码不能为空")),
        ("002", Warning("账号或密码错误")),
    ]
    response_schema = LoginResponseSchema

    @staticmethod
    async def api(
        request: HttpRequest,
        params: LoginRequestSchema = Body(..., description="登录参数"),
    ):
        username = params.username.strip() if params.username else ""
        password = params.password

        if not username or not password:
            raise BusinessException("001")

        # 走 AUTHENTICATION_BACKENDS 配置，会自动命中 MultiFieldAuthBackend
        user = await sync_to_async(authenticate)(
            request,
            username=username,
            password=password,
        )
        if user is None:
            raise BusinessException("002")

        # 建立 Django session，保证 request.user 可用
        await sync_to_async(login)(request, user)

        channel_conf = auth_channel_util.get_channel_config(
            auth_channel_util.resolve_channel_by_request(request)
        )
        token_tag = channel_conf["token_tag"]
        token_read_from = channel_conf["read_from"]
        token_write_to = channel_conf["write_to"]
        return_token_in_body = channel_conf["return_token_in_body"]

        token, jti = token_util.create_token_with_jti(
            payload={
                "uid": user.pk,
                "client": channel_conf["channel"],
            },
            secret=SECRET_KEY,
            expire_seconds=TOKEN_EXPIRE,
        )
        token_util.register_sso_session(
            user_id=user.pk,
            channel=channel_conf["channel"],
            jti=jti,
            max_sessions=token_util.get_sso_max_sessions(channel_conf["channel"]),
            expire_seconds=TOKEN_EXPIRE,
        )

        response_data = SuccessResponse(
            msg="登录成功",
            data=LoginResponseSchema(
                uid=user.pk,
                username=user.username,
                full_name=getattr(user, "full_name", None),
                phone=getattr(user, "phone", None),
                channel=channel_conf["channel"],
                token_tag=token_tag,
                token_origin=token_read_from[0] if token_read_from else None,
                token_read_from=token_read_from,
                token_write_to=token_write_to,
                token_expire=TOKEN_EXPIRE,
                token=token if return_token_in_body else None,
            ).model_dump(),
        ).model_dump()

        response = JsonResponse(response_data, status=200)
        token_util.set_token_by_origins(response, token_tag, token, token_write_to)
        return response
