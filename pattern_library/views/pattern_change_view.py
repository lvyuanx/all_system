# -*-coding:utf-8 -*-

"""
# File       : pattern_change_view.py
# Time       : 2026-03-04 23:59:17
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 更新版式信息
"""
from typing import List, Optional

from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from core.common.utils import res_util
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import (BaseApi, File, Form, HttpRequest,
                                        UploadedFile)
from main.enums import ResCategoryEnum
from pattern_library.models import Pattern, PatternCategory
from pattern_library.utils import image_util


@transaction.atomic
def do(
    request: HttpRequest,
    pattern: Pattern,
    code: Optional[str],
    category: Optional[PatternCategory],
    memo: Optional[str],
    tags: Optional[List[str]],
    main_image: Optional[UploadedFile],
    images: Optional[List[UploadedFile]],
    is_active: Optional[bool],
    undelete_image_ids: Optional[List[int]],
    undelete_main_image_id: Optional[int],
):
    
    if not undelete_main_image_id:
        res_util.unactive_res(pattern.main_image)
    
    for image in list(pattern.images.all()):
        if image.pk not in (undelete_image_ids or []):
            res_util.unactive_res(image)
            pattern.images.remove(image)
    
    # 修改
    if code:
        pattern.code = code
    if category is not None:
        pattern.category = category
    pattern.memo = memo
    pattern.tags = Pattern.generate_tags(*(tags or [])) or ""
    pattern.is_active = is_active
    pattern.save()
    

    # 处理主图
    if main_image:
        main_image = image_util.compress_uploaded_image_lossless(main_image)
        main_res_id = res_util.upload_res(
            request_or_uid=request,
            files=main_image,
            content_type=ContentType.objects.get_for_model(Pattern),
            obj=pattern,
            category=ResCategoryEnum.版型库
        )
        pattern.main_image_id = main_res_id
        pattern.save()

    # 处理辅图
    if images:
        images = image_util.compress_uploaded_images_lossless(images)
        image_ids = res_util.upload_res(
            request_or_uid=request,
            files=images,
            content_type=ContentType.objects.get_for_model(Pattern),
            obj=pattern,
            category=ResCategoryEnum.版型库
        )
        pattern.images.add(*image_ids)

    return pattern


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "更新版式信息失败"
    response_schema = None
    error_codes = [
        ("001", "版式不存在"),
        ("002", "版式类别不存在"),
        ("003", "版式[{code}]已经存在"),
        ("004", "pattern_id 或 code 至少传一个"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        code: Optional[str] = Form(None, description="版号"),
        pattern_id: Optional[int] = Form(None, description="版式ID"),
        category_id: Optional[int] = Form(None, description="类别ID"),
        memo: Optional[str] = Form(None, description="备注"),
        tags: Optional[List[str]] = Form(None, description="标签"),
        main_image: Optional[UploadedFile | int] = File(None, description="主图"),
        is_active: Optional[bool] = Form(True, description="是否启用"),
        images: Optional[List[UploadedFile| int]] = File(None, description="辅图"),
        image_ids: Optional[List[int]] = Form(None, description="辅图ids"),
        main_image_id: Optional[int] = Form(None, description="主图id"),
    ):
        clean_code = (code or "").strip()
        if not pattern_id and not clean_code:
            raise BusinessException("004")

        if pattern_id:
            manager = Pattern.objects.filter(pk=pattern_id, is_delete=False)
        else:
            manager = Pattern.objects.filter(code=clean_code, is_delete=False)
        if not await manager.aexists():
            raise BusinessException("001", {"code": clean_code})

        pattern = await manager.afirst()
        new_code = None
        if clean_code and clean_code != pattern.code:
            if await Pattern.objects.filter(code=clean_code, is_delete=False).exclude(pk=pattern.pk).aexists():
                raise BusinessException("003", {"code": clean_code})
            new_code = clean_code

        category = None
        if category_id:
            category_manager = PatternCategory.objects.filter(
                pk=category_id,
                is_delete=False,
                is_active=True,
            )
            if not await category_manager.aexists():
                raise BusinessException("002")
            category = await category_manager.afirst()
        
        await sync_to_async(do)(
            pattern=pattern,
            request=request,
            code=new_code,
            category=category,
            memo=memo,
            main_image=main_image,
            images=images,
            tags=tags,
            is_active=is_active,
            undelete_image_ids=image_ids,
            undelete_main_image_id=main_image_id,
        )
