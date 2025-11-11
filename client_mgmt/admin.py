from django import forms
from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html_join


from core.admin_extra import AdminBaseMixin
from core.admin_extra.mixins import AdminListImagePreviewMixin
from core.admin_extra.widgets import PCDWidget, FileUploadWidget, HiddenFileInput
from site_mgmt.admin_extra.mixins import SiteFilterMixin
from .models import Client


@admin.register(Client)
class ClientAdmin(AdminBaseMixin, AdminListImagePreviewMixin, SiteFilterMixin, admin.ModelAdmin):
    
    site_field_name = "sites"

    class ClientAdminForm(forms.ModelForm):
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
        
        company_logo_upload = forms.CharField(
            label="公司LOGO",
            required=False,
            widget=FileUploadWidget(
                attrs={
                    "context": {
                        "file_field_name": "company_logo",
                    },
                    "origin_attrs": [
                        "company_logo",
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
                "company_logo"
            ]:
                if field in self._errors:
                    del self._errors[field]
            return cleaned_data

        class Meta:
            model = Client
            fields = "__all__"
            widgets = {
                "address_province": forms.HiddenInput(),
                "address_city": forms.HiddenInput(),
                "address_district": forms.HiddenInput(),
                "address_detail": forms.HiddenInput(),
                "company_logo": HiddenFileInput(),
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['company_logo'].label = ''  # 隐藏label
            

    form = ClientAdminForm

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
            
            form.base_fields["company_logo_upload"].widget.attrs.update(
                {
                    "company_logo": f'{settings.MEDIA_URL}{getattr(obj, "company_logo", "")}',
                }
            )
        return form

    image_preview = {"company_logo": "头像"}
    list_display = (
        "company_logo_preview",
        "from_site",
        "client_name",
        "client_phone",
        "client_sex",
        "company_name",
        "full_address",
        "unfinished_order_total",
        "is_active",
    )
    list_filter = ("company_name",)
    search_fields = ("client_name", "client_phone")
    readonly_fields = (
        "total_amount",
        "total_arrears",
        "total_order_count",
        "total_end_order_count",
    )
    list_display_links = []
    sortable_by = ("client_name",)
    autocomplete_fields = ("address_province", "address_city", "address_district")

    @admin.display(description="未结束订单数")
    def unfinished_order_total(self, obj):
        return obj.total_order_count - obj.total_end_order_count

    
    @admin.display(description="所属站点")
    def from_site(self, obj):
        sites = obj.sites.all()
        if not sites:
            return ""
        return format_html_join(
            '',
            '<span style="display:inline-block; background:#ccc; color:#000; border-radius:4px; padding:4px 6px; margin:2px; font-size:12px;">{}</span>',
            ((site.site_name,) for site in sites)
        )

    @admin.display(description="地址")
    def full_address(self, obj):
        return (
            (str(obj.address_province or ""))
            + (str(obj.address_city or ""))
            + (str(obj.address_district or ""))
            + (str(obj.address_detail or ""))
        )

    def get_list_display_links(self, request: HttpRequest, list_display):
        if request.user.is_superuser:
            return ("client_name",)
        return self.list_display
        