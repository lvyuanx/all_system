# -*-coding:utf-8 -*-

"""
# File       : pattern_info_view.py
# Description: 查询版式详情
"""

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from pattern_library.models import Pattern
from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
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
            await manager.select_related("main_image", "category")
            .prefetch_related("images")
            .afirst()
        )

        # 2️⃣ 主图 URL 处理（防止 None 报错）
        main_image = None
        if pattern.main_image and pattern.main_image.file:
            file = pattern.main_image.file
            main_image = schemas.EchoImageDataSchema(name=file.name, url=file.url, rid=pattern.main_image_id)

        # 3️⃣ 辅图 URL 列表
        images = []
        async for img in pattern.images.all():
            if img.file:
                file = img.file
                image = schemas.EchoImageDataSchema(name=file.name, url=file.url, rid=img.pk)
                images.append(image)

        # 4️⃣ 返回 schema 对应结构
        return {
            "id": pattern.pk,
            "code": pattern.code,
            "category_id": pattern.category_id,
            "category_name": pattern.category.name if pattern.category else None,
            "memo": pattern.memo,  # 允许 None，你 schema 已经写成 str | None
            "is_active": pattern.is_active,
            "tags": pattern.tags_lst,  # 自动转 list[str]
            "main_image": main_image,
            "images": images,
        }
