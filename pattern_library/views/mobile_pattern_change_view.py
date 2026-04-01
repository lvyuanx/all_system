# -*-coding:utf-8 -*-

"""
# File       : mobile_pattern_change_view.py
# Description: 移动端编辑版式信息
"""

from typing import List, Optional

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import (BaseApi, File, Form, HttpRequest,
                                        UploadedFile)
from pattern_library.models import Pattern
from pattern_library.views.pattern_change_view import do


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    finally_code = "000", "编辑版式失败"
    response_schema = None
    error_codes = [
        ("001", "版式不存在"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        code: str = Form(..., description="版号"),
        memo: Optional[str] = Form(None, description="备注"),
        tags: Optional[List[str]] = Form(None, description="标签"),
        main_image: Optional[UploadedFile | int] = File(None, description="主图"),
        is_active: Optional[bool] = Form(True, description="是否启用"),
        images: Optional[List[UploadedFile | int]] = File(None, description="辅图"),
        image_ids: Optional[List[int]] = Form(None, description="保留的辅图ids"),
        main_image_id: Optional[int] = Form(None, description="保留的主图id"),
    ):
        manager = Pattern.objects.filter(code=code, is_delete=False)
        if not await manager.aexists():
            raise BusinessException("001", {"code": code})

        # mobile may pass existing resource ids in file fields; normalize to id lists
        if isinstance(main_image, int):
            if main_image_id is None:
                main_image_id = main_image
            main_image = None

        normalized_image_ids: List[int] = list(image_ids or [])
        normalized_images: Optional[List[UploadedFile]] = None
        if images:
            normalized_images = []
            for item in images:
                if isinstance(item, int):
                    normalized_image_ids.append(item)
                else:
                    normalized_images.append(item)
            if not normalized_images:
                normalized_images = None

        if normalized_image_ids:
            normalized_image_ids = list({int(i) for i in normalized_image_ids})

        await sync_to_async(do)(
            pattern=await manager.afirst(),
            request=request,
            memo=memo,
            main_image=main_image,
            images=normalized_images,
            tags=tags or [],
            is_active=is_active,
            undelete_image_ids=normalized_image_ids or None,
            undelete_main_image_id=main_image_id,
        )
