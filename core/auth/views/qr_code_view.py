# -*-coding:utf-8 -*-
"""
文本转二维码测试接口
"""
from django.http import HttpResponse
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.utils.qr_code_util import generate_qr_png_bytes


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["GET"]
    wrap_response = False  # 直接返回图片流
    finally_code = "000", "生成二维码失败"
    error_codes = [
        ("001", "文本不能为空"),
    ]

    @staticmethod
    async def api(request: HttpRequest, text: str = Query(..., description="要生成二维码的文本")):
        if not text:
            raise BusinessException("001")
        png_bytes = generate_qr_png_bytes(text)
        return HttpResponse(png_bytes, content_type="image/png")
