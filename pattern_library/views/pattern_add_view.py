from asgiref.sync import sync_to_async
from typing import List, Optional
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Form, UploadedFile, File
from main.enums import ResCategoryEnum
from pattern_library.models import Pattern, PatternCategory
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from core.common.utils import res_util
from pattern_library.utils import image_util
from pattern_library.services import consume_next_pattern_code


@transaction.atomic
def do(
    request: HttpRequest,
    category: PatternCategory,
    code: str,
    memo: Optional[str],
    tags: Optional[List[str]],
    main_image: Optional[UploadedFile],
    images: Optional[List[UploadedFile]],
    is_active: Optional[bool],
):
    
    # 创建 Pattern
    pattern = Pattern(
        code=code,
        category=category,
        memo=memo,
        tags=Pattern.generate_tags(*(tags or [])),
        is_active=is_active,
    )
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
    error_codes = [
        ("001", "版式[{code}]已经存在"),
        ("002", "版式类别不存在"),
        ("003", "category_id 不能为空"),
    ]

    @staticmethod
    async def api(
        request: HttpRequest,
        category_id: int = Form(..., description="类别ID"),
        code: Optional[str] = Form(None, description="版号"),
        memo: Optional[str] = Form(None, description="备注"),
        tags: Optional[List[str]] = Form(None, description="标签"),
        main_image: Optional[UploadedFile] = File(None, description="主图"),
        is_active: Optional[bool] = Form(True, description="是否启用"),
        images: Optional[List[UploadedFile]] = File(None, description="辅图"),
    ):
        if not category_id:
            raise BusinessException("003")
        category_manager = PatternCategory.objects.filter(
            pk=category_id,
            is_delete=False,
            is_active=True,
        )
        if not await category_manager.aexists():
            raise BusinessException("002")
        category = await category_manager.afirst()

        final_code = (code or "").strip()
        if not final_code:
            final_code = await sync_to_async(consume_next_pattern_code)(category)
        elif await Pattern.objects.filter(code=final_code).aexists():
            raise BusinessException("001", {"code": final_code})

        await sync_to_async(do)(
            request=request,
            category=category,
            code=final_code,
            memo=memo,
            main_image=main_image,
            images=images,
            tags=tags,
            is_active=is_active,
        )
