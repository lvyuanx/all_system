# -*-coding:utf-8 -*-

"""
# File       : token_util.py
# Time       : 2025-07-27 23:14:25
# Author     : lyx
# version    : python 3.11
# Description: token工具
"""
import time
from abc import ABC, abstractmethod

import orjson
import jwt
from jwt import PyJWTError
from django.http import HttpRequest, HttpResponse


from core.conf import settings

class BaseTokenHandler(ABC):
    @abstractmethod
    def set(self, response: HttpResponse, token_name: str, token: str):
        """设置 token 到 response"""
        pass

    @abstractmethod
    def get(self, request: HttpRequest, token_name: str):
        """从 request 中获取 token"""
        pass

    @abstractmethod
    def remove(self, response: HttpResponse, token_name: str):
        """从 response 中清除 token"""
        pass


class CookieTokenHandler(BaseTokenHandler):
    def set(self, response: HttpResponse, token_name: str, token: str):
        response.set_cookie(token_name, token, httponly=True, samesite='Lax')

    def get(self, request: HttpRequest, token_name: str):
        return request.COOKIES.get(token_name)

    def remove(self, response: HttpResponse, token_name: str):
        response.delete_cookie(token_name)


class HeaderTokenHandler(BaseTokenHandler):
    def set(self, response: HttpResponse, token_name: str, token: str):
        response[token_name] = f"Bearer {token}"

    def get(self, request: HttpRequest, token_name: str):
        raw = request.META.get(f"HTTP_{token_name.upper().replace('-', '_')}")
        if raw and raw.startswith("Bearer "):
            return raw[7:]
        return raw

    def remove(self, response: HttpResponse, token_name: str):
        # 设置空字符串表示删除 header（虽然 HTTP 本身没有“删除 header”的标准做法）
        response[token_name] = ''


class QueryTokenHandler(BaseTokenHandler):
    def set(self, response: HttpResponse, token_name: str, token: str):
        # Query 参数不能设置在响应中
        pass

    def get(self, request: HttpRequest, token_name: str):
        return request.GET.get(token_name)

    def remove(self, response: HttpResponse, token_name: str):
        # 无法清除查询参数，仅保留方法签名
        pass


class BodyTokenHandler(BaseTokenHandler):
    def set(self, response: HttpResponse, token_name: str, token: str):
        # 无法在响应中设置 body，仅保留方法签名
        pass

    def get(self, request: HttpRequest, token_name: str):
        try:
            content_type = request.META.get("CONTENT_TYPE", "")
            if "application/json" in content_type:
                data = orjson.loads(request.body)
                return data.get(token_name)
            elif "application/x-www-form-urlencoded" in content_type:
                return request.POST.get(token_name)
        except Exception:
            return None

    def remove(self, response: HttpResponse, token_name: str):
        # 无法清除请求体参数，仅保留方法签名
        pass


tk_handler_dict = {
    "cookie": CookieTokenHandler(),
    "header": HeaderTokenHandler(),
    "query": QueryTokenHandler(),
    "body": BodyTokenHandler(),
}


def create_token(payload: dict, secret: str, expire_seconds: int = settings.TOKEN_EXPIRE) -> str:
    """
    生成 JWT Token
    :param payload: dict 负载数据
    :param secret: str 签名密钥
    :param expire_seconds: int 过期时间（秒）
    :return: str JWT token
    """
    payload = payload.copy()
    payload['exp'] = int(time.time()) + expire_seconds
    token = jwt.encode(payload, secret, algorithm='HS256')
    # PyJWT 2.x 返回 str，1.x 返回 bytes，兼容处理
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def verify_token(token: str, secret: str) -> dict:
    """
    校验 JWT Token
    :param token: str JWT token
    :param secret: str 签名密钥
    :return: dict 解码后的payload
    :raises jwt.PyJWTError: 校验失败抛出异常
    """
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except PyJWTError as e:
        raise e



