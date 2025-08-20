# -*-coding:utf-8 -*-

"""
# File       : status_code_middleware.py
# Time       : 2025-08-01 10:50:25
# Author     : lyx
# version    : python 3.11
# Description: 状态码中间件
"""
import logging
from django.http import HttpRequest, HttpResponse, JsonResponse

from core.ninja_extra.response_schema import ErrorResponse
from core.conf import settings

logger = logging.getLogger(__name__)
NINJA_BASE_URL = settings.NINJA_BASE_URL

class StatusCodeMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        
    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        if request.path.startswith(NINJA_BASE_URL):
            if isinstance(response, HttpResponse):
                status_code = response.status_code
                if status_code != 200:
                    return JsonResponse(ErrorResponse(
                        code=str(status_code),
                        msg=response.reason_phrase
                    ).model_dump(), status=200)
        
        return response
