# -*-coding:utf-8 -*-

"""
# File       : mobile_pattern_add_view.py
# Description: mobile add pattern
"""

from typing import List, Optional

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, File, Form, HttpRequest, UploadedFile
from pattern_library.models import Pattern
from pattern_library.views.pattern_add_view import do


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["POST"]
    finally_code = "000", "add pattern failed"
    response_schema = None
    error_codes = [("001", "pattern [{code}] already exists")]

    @staticmethod
    async def api(
        request: HttpRequest,
        code: str = Form(..., description="pattern code"),
        memo: Optional[str] = Form(None, description="memo"),
        tags: Optional[List[str]] = Form(None, description="tags"),
        main_image: Optional[UploadedFile | int] = File(None, description="main image"),
        is_active: Optional[bool] = Form(True, description="is active"),
        images: Optional[List[UploadedFile | int]] = File(None, description="images"),
    ):
        if await Pattern.objects.filter(code=code, is_delete=False).aexists():
            raise BusinessException("001", {"code": code})

        # mobile may pass existing resource ids in file fields; normalize to id lists
        if isinstance(main_image, int):
            # for add, keeping an existing main image id is enough; do() accepts UploadedFile
            # so we treat id as no-upload and set it after creation
            main_image_id = main_image
            main_image = None
        else:
            main_image_id = None

        normalized_image_ids: List[int] = []
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

        pattern = await sync_to_async(do)(
            request=request,
            code=code,
            memo=memo,
            main_image=main_image,
            images=normalized_images,
            tags=tags or [],
            is_active=is_active,
        )

        # attach existing resource ids if provided
        if main_image_id:
            pattern.main_image_id = main_image_id
            await sync_to_async(pattern.save)()
        if normalized_image_ids:
            await sync_to_async(pattern.images.add)(*list({int(i) for i in normalized_image_ids}))
