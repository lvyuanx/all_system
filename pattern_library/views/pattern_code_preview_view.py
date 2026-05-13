# -*-coding:utf-8 -*-

"""
# File       : pattern_code_preview_view.py
# Description: 预览自动生成版号
"""

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from asgiref.sync import sync_to_async
from pattern_library.models import PatternCategory
from pattern_library.services import build_pattern_code_preview

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "预览自动版号失败"
    response_schema = schemas.PatternCodePreviewSchema
    error_codes = [
        ("001", "版式类别不存在"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        category_id: int = Query(..., description="类别ID"),
    ):
        manager = PatternCategory.objects.filter(
            pk=category_id,
            is_delete=False,
            is_active=True,
        )
        if not await manager.aexists():
            raise BusinessException("001")
        category = await manager.afirst()
        preview_code = await sync_to_async(build_pattern_code_preview)(category)
        return {"preview_code": preview_code}
