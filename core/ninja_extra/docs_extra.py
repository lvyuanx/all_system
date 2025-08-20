# -*-coding:utf-8 -*-

"""
# File       : docs_extra.py
# Time       : 2025-07-25 14:10:08
# Author     : lyx
# version    : python 3.11
# Description: 自定义 API 文档页面
"""
from django.shortcuts import render
from core.conf import settings
import urllib.parse

def api_docs(request):
    """
    自定义 API 文档页面
    """
    openapi_url = urllib.parse.urljoin(settings.NINJA_BASE_URL, "openapi.json")
    context = {
        "openapi_url": openapi_url if openapi_url.startswith("/") else f"/{openapi_url}",
    }
    return render(request, 'swagger.html', context)