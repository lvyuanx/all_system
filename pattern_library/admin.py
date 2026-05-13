import json
import os
from urllib.parse import unquote, urlparse

from django import forms
from django.contrib import admin
from django.db import transaction
from django.utils.html import format_html_join

from core.admin_extra.mixins import AdminListImagePreviewMixin, AuditAdminMixin
from core.common.utils import res_util
from main.enums import ResCategoryEnum

from .models import Pattern, PatternCategory, PatternCategorySerial


@admin.register(Pattern)
class PatternAdmin(AdminListImagePreviewMixin, AuditAdminMixin, admin.ModelAdmin):
    
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
        "category",
        "memo",
        "tags_display",
        "is_active",
        "main_image_preview",
    )
    
    search_fields = ("code", "tags", "memo", "category__name")
    list_filter = ("category", "is_active")
    
    @admin.display(description="标签")
    def tags_display(self, obj: Pattern):
        tags_lst = obj.tags_lst
        if not tags_lst:
            return ""
        return format_html_join(
            '',
            '<span style="display:inline-block; background:#ccc; color:#000; border-radius:4px; padding:4px 6px; margin:2px; font-size:12px;">{}</span>',
            ((tag,) for tag in tags_lst)
        )


@admin.register(PatternCategory)
class PatternCategoryAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "code_prefix",
        "date_mode",
        "serial_digits",
        "is_active",
        "update_time",
    )
    search_fields = ("name", "code_prefix")
    list_filter = ("date_mode", "is_active")


@admin.register(PatternCategorySerial)
class PatternCategorySerialAdmin(admin.ModelAdmin):
    list_display = ("category", "date_key", "current_serial", "update_time")
    search_fields = ("category__name", "date_key")
    list_filter = ("category",)
    readonly_fields = ("category", "date_key", "current_serial", "update_time")
