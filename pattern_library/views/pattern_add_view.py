from asgiref.sync import sync_to_async
from typing import List, Optional
from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Form, UploadedFile, File
from pattern_library.models import Pattern
from core.common.models import Resource
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
import uuid, mimetypes, os
from . import schemas


def save_uploaded_file(uploaded_file: UploadedFile, category: str, uploader=None) -> Resource:
    """
    保存上传文件到 Resource 表
    """
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1]
    name = f"{uuid.uuid4().hex}{ext}"

    # 保存 Resource 实例
    resource = Resource(
        name=filename,
        stored_name=name,
        file_type=mimetypes.guess_type(filename)[0],
        size=len(uploaded_file.read()),
        category=category,
        uploader=uploader,
    )
    # 保存文件到 FileField
    resource.file.save(name, uploaded_file, save=True)
    return resource


@transaction.atomic
def do(
    request: HttpRequest,
    code: str,
    memo: Optional[str],
    tags: Optional[List[str]],
    main_image: Optional[UploadedFile],
    images: Optional[List[UploadedFile]],
):
    
    # 创建 Pattern
    
    pattern = Pattern(code=code, memo=memo, tags=Pattern.generate_tags(*tags))
    pattern.save()  # 先保存，不然 M2M 不能添加

    # 处理主图
    if main_image:
        main_res = save_uploaded_file(main_image, category="主图", uploader=request.user)
        pattern.main_image = main_res
        pattern.save()

    # 处理辅图
    if images:
        for img in images:
            res = save_uploaded_file(img, category="辅图", uploader=request.user)
            pattern.images.add(res)

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
        )