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
    
    
    class AdminForm(forms.ModelForm):

        image_upload = forms.FileField(
            label="主图",
            required=True,
            widget=ImageUploadWidget(
                attrs={
                    "context": {
                        "model_name": "pattern"
                    }
                }
            ),
        )
        
        images_upload = forms.FileField(
            label="辅图",
            required=False,
            widget=MultiImageUploadWidget(
                attrs={
                    "context": {
                        "model_name": "pattern"
                    }
                }
            ),
        )
        
        def clean(self):
            cleaned_data = super().clean()
            
            main_image = self.files.get("image_upload")
            main_image_url  =  self.data.get("image_upload", None)

            if not main_image_url and not main_image:
                return cleaned_data
            
            # 移除隐藏字段的错误
            for field in [
                "image_upload",
            ]:
                if field in self._errors:
                    del self._errors[field]
            return cleaned_data
        
        class Meta:
            model = Pattern
            exclude = ("main_image", "images")
    
    form = AdminForm
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            images = obj.images.all().order_by("id")
            image_urls = [common_util.media_url(image) for image in images]
            form.base_fields["image_upload"].widget.attrs.update(
                {
                    "field_value": common_util.media_url(getattr(obj, "main_image", None)),
                }
            )
            form.base_fields["images_upload"].widget.attrs.update(
                {
                    "field_value": image_urls,
                }
            )
        else:
            # 注意，这一步不能省略，会导致field_value出现缓存
            form.base_fields["image_upload"].widget.attrs.update(
                {
                    "field_value": "",
                }
            )
            form.base_fields["images_upload"].widget.attrs.update(
                {
                    "field_value": [],
                }
            )
        
        return form
    
    
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
        "name",
        "code",
        "memo",
        "main_image_preview",
    )
    
    search_fields = ("code", "name")