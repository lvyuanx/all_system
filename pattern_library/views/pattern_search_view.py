# -*-coding:utf-8 -*-

"""
# File       : pattern_search_view.py
# Time       : 2026-03-13 16:15:29
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 根据图库搜索查询数据
"""

from django.db.models import Q
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.common.models import Resource
from main.enums import ResCategoryEnum
from pattern_library.models import Pattern
from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "根据图库搜索查询数据失败"
    response_schema = schemas.PatternInfoSchema | None
    error_codes = [
        ("001", "资源不存在"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        filename: str = Query(..., description="资源名称"),
    ):
        manager = Resource.objects.filter(
            stored_name=filename, category=ResCategoryEnum.版型库
        ).values("id")

        if not await manager.aexists():
            return
        
        res = await manager.afirst()
        res_id = res["id"]
        
        pattern = (
            Pattern.objects
            .filter(is_delete=False)
            .filter(
                Q(main_image_id=res_id) | Q(images__id=res_id)
            )
        )

        if not await pattern.aexists():
            return
        
        pattern = (
            await pattern
            .select_related("main_image", "category")
            .prefetch_related("images")
            .afirst()
        )

        # 主图 URL 处理（防止 None 报错）
        main_image = None
        if pattern.main_image and pattern.main_image.file:
            file = pattern.main_image.file
            main_image = schemas.EchoImageDataSchema(name=file.name, url=file.url, rid=pattern.main_image_id)

        # 辅图 URL 列表
        images = []
        async for img in pattern.images.all():
            if img.file:
                file = img.file
                image = schemas.EchoImageDataSchema(name=file.name, url=file.url, rid=img.pk)
                images.append(image)

        # 返回 schema 对应结构
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
