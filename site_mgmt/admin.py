from django.contrib import admin


from django import forms
from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest


from core.admin_extra import AdminBaseMixin
from core.admin_extra.mixins import AdminListImagePreviewMixin
from core.admin_extra.widgets import PCDWidget, FileUploadWidget, HiddenFileInput
from .models import SysSite, SiteAddress


@admin.register(SysSite)
class SysSiteAdmin(AdminBaseMixin, AdminListImagePreviewMixin, admin.ModelAdmin):

    class SysSiteAdminForm(forms.ModelForm):
        logo_upload = forms.CharField(
            label="站点LOGO",
            required=False,
            widget=FileUploadWidget(
                attrs={
                    "context": {
                        "file_field_name": "site_logo",
                    },
                    "origin_attrs": [
                        "site_logo",
                    ]
                }
            ),
        )

        def clean(self):
            cleaned_data = super().clean()
            # 移除隐藏字段的错误
            for field in [
                "site_logo"
            ]:
                if field in self._errors:
                    del self._errors[field]
            return cleaned_data

        class Meta:
            model = SysSite
            fields = "__all__"
            widgets = {
                "site_logo": HiddenFileInput(),
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['site_logo'].label = ''  # 隐藏label
            

    form = SysSiteAdminForm

    def get_form(self, request, obj=None, **kwargs):
        """在编辑模式下注入省市区的 code"""
        form = super().get_form(request, obj, **kwargs)
        if obj:

            def safe_code(value):
                # 安全地提取 code 或 id
                if not value:
                    return ""
                return getattr(value, "id", "")
            
            form.base_fields["logo_upload"].widget.attrs.update(
                {
                    "site_logo": f'{settings.MEDIA_URL}{getattr(obj, "site_logo", "")}',
                }
            )
        return form

    image_preview = {"site_logo": "头像"}
    list_display = (
        "site_logo_preview",
        "site_name",
    )
    list_filter = ("site_name",)
    search_fields = ("site_name",)
    list_display_links = ["site_name"]
    sortable_by = ("site_name",)
    



@admin.register(SiteAddress)
class SiteAddressAdmin(AdminBaseMixin, AdminListImagePreviewMixin, admin.ModelAdmin):

    class SiteAddressAdminForm(forms.ModelForm):
        linkage = forms.CharField(
            label="地址",
            required=False,
            widget=PCDWidget(
                attrs={
                    "origin_attrs": [
                        "address_province",
                        "address_city",
                        "address_district",
                        "address_detail",
                    ]
                }
            ),
        )
        

        def clean(self):
            cleaned_data = super().clean()
            # 移除隐藏字段的错误
            for field in [
                "address_province",
                "address_city",
                "address_district",
                "address_detail",
            ]:
                if field in self._errors:
                    del self._errors[field]
            return cleaned_data

        class Meta:
            model = SiteAddress
            fields = "__all__"
            widgets = {
                "address_province": forms.HiddenInput(),
                "address_city": forms.HiddenInput(),
                "address_district": forms.HiddenInput(),
                "address_detail": forms.HiddenInput(),
            }
            

    form = SiteAddressAdminForm

    def get_form(self, request, obj=None, **kwargs):
        """在编辑模式下注入省市区的 code"""
        form = super().get_form(request, obj, **kwargs)
        if obj:

            def safe_code(value):
                # 安全地提取 code 或 id
                if not value:
                    return ""
                return getattr(value, "id", "")

            form.base_fields["linkage"].widget.attrs.update(
                {
                    "address_province": safe_code(obj.address_province),
                    "address_city": safe_code(obj.address_city),
                    "address_district": safe_code(obj.address_district),
                    "address_detail": getattr(obj, "address_detail", ""),
                }
            )
        return form

    list_display = (
        "site_name",
        "full_address",
    )
    search_fields = ("full_address", )
    list_display_links = ["site_name", ]
    
    
    @admin.display(description="地址")
    def full_address(self, obj):
        return (
            (str(obj.address_province or ""))
            + (str(obj.address_city or ""))
            + (str(obj.address_district or ""))
            + (str(obj.address_detail or ""))
        )
    
    
    @admin.display(description="站点名称")
    def site_name(self, obj):
        return obj.site.site_name
