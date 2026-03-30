# -*-coding:utf-8 -*-

"""
# File       : admin_login_view.py
# Description: 管理端登录接口
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

        user = await sync_to_async(authenticate)(
            request,
            username=username,
            password=password,
        )
        if user is None:
            raise BusinessException("002")

        await sync_to_async(login)(request, user)

        channel_conf = auth_channel_util.get_channel_config("admin")
        token_tag = channel_conf["token_tag"]
        token_read_from = channel_conf["read_from"]
        token_write_to = channel_conf["write_to"]
        return_token_in_body = channel_conf["return_token_in_body"]

        token = token_util.create_token(
            payload={
                "uid": user.pk,
                "client": "admin",
            },
            secret=SECRET_KEY,
            expire_seconds=TOKEN_EXPIRE,
        )

        response_data = SuccessResponse(
            msg="登录成功",
            data=LoginResponseSchema(
                uid=user.pk,
                username=user.username,
                full_name=getattr(user, "full_name", None),
                phone=getattr(user, "phone", None),
                channel="admin",
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
