# -*-coding:utf-8 -*-

"""
# File       : mobile_pattern_deactivate_view.py
# Description: 移动端下架版式（is_active=False）
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, Body, HttpRequest
from pattern_library.models import Pattern

from pydantic import BaseModel, Field


class DeactivateSchema(BaseModel):
    pattern_id: int = Field(..., description="版式ID")


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    finally_code = "000", "下架版式失败"
    response_schema = None
    error_codes = [
        ("001", "版式不存在"),
        ("002", "版式已下架"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        params: DeactivateSchema = Body(..., description="下架参数"),
    ):
        manager = Pattern.objects.filter(pk=params.pattern_id, is_delete=False)

        if not await manager.aexists():
            raise BusinessException("001")

        pattern = await manager.afirst()

        if not pattern.is_active:
            raise BusinessException("002")

        pattern.is_active = False
        await sync_to_async(pattern.save)()
