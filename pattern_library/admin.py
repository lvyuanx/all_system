import json
import os
from urllib.parse import unquote, urlparse
from django import forms
from django.contrib import admin

from django.db import transaction
from core.admin_extra.widgets import ImageUploadWidget, MultiImageUploadWidget
from core.admin_extra.mixins import AdminListImagePreviewMixin
from core.common.utils import res_util
from .models import Pattern
from main.enums import ResCategoryEnum
from core.utils import common_util


@admin.register(Pattern)
class PatternAdmin(AdminListImagePreviewMixin, admin.ModelAdmin):
    
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        # 主图
        main_image = request.FILES.get("image_upload", None)
        if main_image and obj.main_image != main_image:
            if obj.main_image:  # 删除旧图片
                res_util.unactive_res(obj.main_image)
            mres_id = res_util.upload_res(
                request, main_image, ResCategoryEnum.版型库.value, obj=obj
            )
            obj.main_image_id = mres_id
        
        # 副图
        images_deleted = request.POST.get("images_deleted", None)
        if images_deleted:
            images_deleted = json.loads(images_deleted)
            # 获取删除的文件名称
            images_deleted_names = []
            for image_deleted in images_deleted:
                path = urlparse(image_deleted).path
                filename = os.path.basename(path)
                filename = unquote(filename)
                images_deleted_names.append(filename)
            # 解除res的关联
            images_to_remove = obj.images.filter(name__in=images_deleted_names)
            obj.images.remove(*images_to_remove)
            res_util.batch_unactive_res(images_to_remove)

        
        images = request.FILES.getlist("images_upload", [])
        for image in images:
            res_id = res_util.upload_res(
                request, image, ResCategoryEnum.版型库.value, obj=obj
            )
            obj.images.add(res_id)
        

        super().save_model(request, obj, form, change)

    
    image_preview = {"main_image": "主图"}
    list_display = (
        "code",
        "memo",
        "main_image_preview",
    )
    
    search_fields = ("code", "name")