# -*-coding:utf-8 -*-

"""
# File       : mobile_pattern_info_view.py
# Description: 移动端查询版式详情
"""

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from pattern_library.models import Pattern

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["GET"]
    finally_code = "000", "查询版式详情失败"
    response_schema = schemas.PatternInfoSchema
    error_codes = [
        ("001", "版式不存在"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, pattern_id: int = Query(..., description="版式ID")
    ):
        manager = Pattern.objects.filter(pk=pattern_id, is_delete=False)

        if not await manager.aexists():
            raise BusinessException("001")

        pattern = (
            await manager.select_related("main_image")
            .prefetch_related("images")
            .afirst()
        )

        main_image = None
        if pattern.main_image and pattern.main_image.file:
            file = pattern.main_image.file
            main_image = schemas.EchoImageDataSchema(name=file.name, url=file.url, rid=pattern.main_image_id)

        images = []
        async for img in pattern.images.all():
            if img.file:
                file = img.file
                images.append(schemas.EchoImageDataSchema(name=file.name, url=file.url, rid=img.pk))

        return {
            "code": pattern.code,
            "memo": pattern.memo,
            "is_active": pattern.is_active,
            "tags": pattern.tags_lst,
            "main_image": main_image,
            "images": images,
        }
