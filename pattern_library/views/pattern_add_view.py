from asgiref.sync import sync_to_async
from typing import List, Optional
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Form, UploadedFile, File
from main.enums import ResCategoryEnum
from pattern_library.models import Pattern
from core.common.models import Resource
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
import uuid, mimetypes, os
from core.common.utils import res_util
from pattern_library.utils import image_util


@transaction.atomic
def do(
    request: HttpRequest,
    code: str,
    memo: Optional[str],
    tags: Optional[List[str]],
    main_image: Optional[UploadedFile],
    images: Optional[List[UploadedFile]],
    is_active: Optional[bool],
):
    
    # 创建 Pattern
    pattern = Pattern(code=code, memo=memo, tags=Pattern.generate_tags(*tags), is_active=is_active)
    pattern.save()  # 先保存，不然 M2M 不能添加

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
    finally_code = "000", "添加版式失败"
    response_schema = None
    error_codes = [("001", "版式[{code}]已经存在")]

    @staticmethod
    async def api(
        request: HttpRequest,
        code: str = Form(..., description="版号"),
        memo: Optional[str] = Form(None, description="备注"),
        tags: Optional[List[str]] = Form(None, description="标签"),
        main_image: Optional[UploadedFile] = File(None, description="主图"),
        is_active: Optional[bool] = Form(True, description="是否启用"),
        images: Optional[List[UploadedFile]] = File(None, description="辅图"),
    ):
        if await Pattern.objects.filter(code=code, is_delete=False).aexists():
            raise BusinessException("001", {"code": code})

        await sync_to_async(do)(
            request=request,
            code=code,
            memo=memo,
            main_image=main_image,
            images=images,
            tags=tags,
            is_active=is_active,
        )