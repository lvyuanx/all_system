import base64
from typing import Optional
from django.contrib.auth import authenticate
from django.http import HttpRequest
from django.contrib.auth.models import User


def check_basic_auth(request: HttpRequest) -> Optional[User]:
    """
    校验 HTTP Basic Auth，如果成功返回 user，否则返回 None
    
    Args:
        request: Django HTTP请求对象
        
    Returns:
        Optional[User]: 认证成功的用户对象，认证失败返回None
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Basic '):
        return None

    try:
        # 获取用户名密码
        encoded_credentials = auth_header.split(' ')[1]
        decoded = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded.split(':', 1)

        # 认证用户
        user = authenticate(request, username=username, password=password)
        return user
    except Exception:
        return None
