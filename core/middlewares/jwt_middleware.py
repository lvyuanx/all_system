# -*-coding:utf-8 -*-

"""
# File       : jwt_middleware.py
# Time       : 2025-07-27 23:09:53
# Author     : lyx
# version    : python 3.11
# Description: jwt校验中间件
"""
import logging

from django.contrib.auth import logout
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from jwt import ExpiredSignatureError

from core.conf import settings
from core.ninja_extra.response_schema import ErrorResponse, ResponseLevel
from core.utils import auth_channel_util, token_util

logger = logging.getLogger(__name__)

SECRET_KEY = settings.SECRET_KEY
NINJA_BASE_URL = settings.NINJA_BASE_URL
API_PREFIX = f"/{NINJA_BASE_URL.strip('/')}/"
PUBLIC_API_PATHS = {
    f"{API_PREFIX}auth/account/login",
    f"{API_PREFIX}mobile/auth/account/login",
}


class JWTMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        req_path = request.path
        normalized_path = req_path.rstrip("/")

        if req_path.startswith("/admin/login/") or req_path.startswith(settings.STATIC_URL) or req_path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        if normalized_path in PUBLIC_API_PATHS:
            return self.get_response(request)

        is_admin = req_path.startswith("/admin/")
        channel = auth_channel_util.resolve_channel_by_request(request)
        channel_conf = auth_channel_util.get_channel_config(channel)
        token = token_util.get_token_by_origins(
            request=request,
            token_name=channel_conf["token_tag"],
            origins=channel_conf["read_from"],
        )
        if not token and hasattr(request, "new_token"):
            token = request.new_token

        if not token:
            if is_admin:
                if request.user.is_authenticated:
                    logout(request)
                return redirect(reverse("admin:login"))
            return JsonResponse(
                ErrorResponse(
                    code="401",
                    msg="未登录",
                    level=ResponseLevel.ERROR,
                ).model_dump(),
                status=200,
            )

        token_payload = {}
        try:
            token_payload = token_util.verify_token(token, SECRET_KEY)
            token_client = token_payload.get("client")
            if token_client and token_client != channel:
                raise ValueError("token client mismatch")
        except ExpiredSignatureError:
            logger.warning(f"token已过期 - {token}")
            if is_admin:
                if request.user.is_authenticated:
                    logout(request)
                return redirect(reverse("admin:login"))
            return JsonResponse(
                ErrorResponse(
                    code="401",
                    msg="未登录",
                    level=ResponseLevel.ERROR,
                ).model_dump(),
                status=200,
            )
        except ValueError:
            logger.warning(f"token channel不匹配 - token_client={token_payload.get('client')}, channel={channel}, path={req_path}")
            if is_admin:
                if request.user.is_authenticated:
                    logout(request)
                return redirect(reverse("admin:login"))
            return JsonResponse(
                ErrorResponse(
                    code="401",
                    msg="未登录",
                    level=ResponseLevel.ERROR,
                ).model_dump(),
                status=200,
            )
        except Exception:
            logger.error(f"token验证失败 - {token}", exc_info=True)
            if is_admin:
                if request.user.is_authenticated:
                    logout(request)
                return redirect(reverse("admin:login"))
            return JsonResponse(
                ErrorResponse(
                    code="404",
                    msg="未登录",
                    level=ResponseLevel.ERROR,
                ).model_dump(),
                status=200,
            )

        return self.get_response(request)
