# -*-coding:utf-8 -*-

"""
# File       : mobile_pattern_activate_view.py
# Description: mobile activate pattern (is_active=True)
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, Body, HttpRequest
from pattern_library.models import Pattern

from pydantic import BaseModel, Field


class ActivateSchema(BaseModel):
    pattern_id: int = Field(..., description="pattern id")


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    finally_code = "000", "activate pattern failed"
    response_schema = None
    error_codes = [
        ("001", "pattern not exist"),
        ("002", "pattern already active"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        params: ActivateSchema = Body(..., description="activate params"),
    ):
        manager = Pattern.objects.filter(pk=params.pattern_id, is_delete=False)

        if not await manager.aexists():
            raise BusinessException("001")

        pattern = await manager.afirst()

        if pattern.is_active:
            raise BusinessException("002")

        pattern.is_active = True
        await sync_to_async(pattern.save)()
