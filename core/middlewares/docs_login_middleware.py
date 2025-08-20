# -*-coding:utf-8 -*-

"""
# File       : docs_login_middleware.py
# Time       : 2025-07-24 00:45:56
# Author     : lyx
# version    : python 3.11
# Description: 文档登录中间件
"""
import logging
from django.http import HttpRequest, HttpResponse, Http404
from jwt import ExpiredSignatureError

from core.utils import http_util, token_util
from core.conf import settings

logger = logging.getLogger(__name__)

TOKEN_ORIGIN = settings.TOKEN_ORIGIN  # token来源
TOKEN_TAG = settings.TOKEN_TAG  # token标记名称
SECRET_KEY = settings.SECRET_KEY
TOKEN_EXPIRE = settings.TOKEN_EXPIRE  # token过期时间
token_handler = token_util.tk_handler_dict[TOKEN_ORIGIN]

class DocsLoginMiddlware:
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        
        new_token = None
        if request.path.startswith("/docs"):  # 对docs开头的请求拦截
            token = token_handler.get(request, TOKEN_TAG)  # 去指定来源获取token
            if not token:
                user = http_util.check_basic_auth(request)  # 通过HTTP Basic的方式认证
                if user: # 认证成功
                    new_token = token_util.create_token(
                        payload={
                            "uid": user.pk,
                        },
                        secret=SECRET_KEY,
                        expire_seconds=TOKEN_EXPIRE
                    ) # 生成token
                    request.new_token = new_token
                else:  # 认证失败
                    return self.return_login_response()
            else: # 校验token
                try:
                    token_util.verify_token(token, SECRET_KEY)
                except ExpiredSignatureError:
                    logger.warning(f'token已过期 - {token}')
                    return self.return_login_response()
                except Exception:
                    logger.warning(f'token验证失败 - {token}')
                    return self.return_login_response()
   

        # 如果用户已认证或认证成功，则继续处理请求
        response = self.get_response(request)
        if new_token:
            token_util.tk_handler_dict[TOKEN_ORIGIN].set(response, TOKEN_TAG, new_token)  # 注入token

        return response
    
    
    def return_login_response(self):
        response = HttpResponse("Unauthorized", status=401)
        # 创建一个401未授权响应
        response['WWW-Authenticate'] = 'Basic realm="DjangoRealm"'
        # 设置WWW-Authenticate头，提示浏览器弹出认证对话框
        token_handler.remove(response, TOKEN_TAG)
        return response
