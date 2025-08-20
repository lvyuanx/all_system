# -*-coding:utf-8 -*-

"""
# File       : jwt_middleware.py
# Time       : 2025-07-27 23:09:53
# Author     : lyx
# version    : python 3.11
# Description: jwt校验中间件
"""
import logging
from django.http import HttpRequest, HttpResponse, JsonResponse
from jwt import ExpiredSignatureError

from core.utils import token_util
from core.conf import settings
from core.ninja_extra.response_schema import ErrorResponse, ResponseLevel

logger = logging.getLogger(__name__)

TOKEN_ORIGIN = settings.TOKEN_ORIGIN  # token来源
TOKEN_TAG = settings.TOKEN_TAG  # token标记名称
SECRET_KEY = settings.SECRET_KEY
TOKEN_EXPIRE = settings.TOKEN_EXPIRE  # token过期时间
token_handler = token_util.tk_handler_dict[TOKEN_ORIGIN]
NINJA_BASE_URL = settings.NINJA_BASE_URL

class JWTMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        
    def __call__(self, request: HttpRequest):
        if not request.path.startswith(NINJA_BASE_URL):  # 只拦截ninja
            return self.get_response(request)
        
        token = token_handler.get(request, TOKEN_TAG)  # 去指定来源获取token
        if not token and hasattr(request, "new_token"):
            token = request.new_token  # token 可能是上层拦截器生成的
            
        if not token:
            return JsonResponse(
                ErrorResponse(
                    code="401", 
                    msg="未登录",
                    level=ResponseLevel.ERROR
                ).model_dump(), 
                status=200
            )
        
        try:
            token  = token_util.verify_token(token, SECRET_KEY)
        except ExpiredSignatureError:
            logger.warning(f'token已过期 - {token}')
            return JsonResponse(
                ErrorResponse(
                    code="401", 
                    msg="未登录",
                    level=ResponseLevel.ERROR
                ).model_dump(), 
                status=200
            )
        except Exception:
            logger.error(f'token验证失败 - {token}', exc_info=True)
            return JsonResponse(
                ErrorResponse(
                    code="404", 
                    msg="未登录",
                    level=ResponseLevel.ERROR
                ).model_dump(), 
                status=200
            )
    
        return self.get_response(request)

    
    
    def return_login_response(self):
        response = HttpResponse("Unauthorized", status=401)
        # 创建一个401未授权响应
        response['WWW-Authenticate'] = 'Basic realm="DjangoRealm"'
        # 设置WWW-Authenticate头，提示浏览器弹出认证对话框
        return response
