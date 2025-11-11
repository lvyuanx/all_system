from django import forms
from django.conf import settings
from django.contrib import admin

from django.contrib import messages
from django.forms import ValidationError
from core.admin_extra.widgets.hidden_file_input import HiddenFileInput
from core.admin_extra.widgets import ImageUploadWidget, MultiImageUploadWidget
from core.common.utils.upload_util import  ResourceAttachContext
from .models import Pattern
from main.enums import ResCategoryEnum
from core.utils import common_util


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    
    
    class AdminForm(forms.ModelForm):
        
        file_field_name = "main_image"

        image_upload = forms.CharField(
            label="主图",
            required=False,
            widget=ImageUploadWidget(
                attrs={
                    "context": {
                        "file_field_name": file_field_name,
                        "file_field_name_proxy": "image_upload",
                    },
                    "widget_conf": {
                        "value_attr_name": file_field_name,
                    }
                }
            ),
        )
        
        multi_image_upload = forms.CharField(
            label="辅图",
            required=False,
            widget=MultiImageUploadWidget(
                attrs={
                    "context": {
                        "file_field_name": file_field_name,
                        "file_field_name_proxy": "multi_image_upload",
                    },
                    "widget_conf": {
                        "value_attr_name": file_field_name,
                    }
                }
            )
        )       
        
        def clean(self):
            cleaned = super().clean()
            # request.FILES 在 form.clean 中不可直接拿到，所以判断逻辑：
            # 1) 新建时必须上传 main_image
            # 2) 编辑时：如果实例已有 main_image_id，则可以不传新文件；否则必须上传
            # 注意：如果你在 admin 里用的是 upload input name="main_image"，可以用 self.files
            uploaded = self.files.get(self.file_field_name) if hasattr(self, "files") else None
            has_existing = bool(getattr(self.instance, f"{self.file_field_name}_id", None))

            if not uploaded and not has_existing:
                # 关联字段级错误
                raise ValidationError({"main_image": "请上传主图文件"})
            else:
                for field in [
                        self.file_field_name
                    ]:
                        if field in self._errors:
                            del self._errors[field]
                return cleaned
        
        class Meta:
            model = Pattern
            fields = "__all__"
            widgets = {
                "main_image": forms.FileInput(),
            }
    
    form = AdminForm
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields["image_upload"].widget.attrs.update(
                {
                    "main_image": common_util.media_url(getattr(obj, "main_image", None)),
                }
            )
        
        return form
    
    
    
    def save_model(self, request, obj, form, change):
        file = request.FILES.get("main_image", None)
        if file:
            with ResourceAttachContext(request.user.pk) as ctx:
                rid = ctx.upload(file, ResCategoryEnum.版型库.value, obj=obj)
                obj.main_image_id = rid
                super().save_model(request, obj, form, change)
                ctx.link(rid, obj.pk)
        else:
            raise ValidationError({"main_image": "请上传主图文件"})

