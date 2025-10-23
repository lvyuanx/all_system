from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpRequest

from core.admin_extra import AdminBaseMixin
from core.admin_extra.mixins import AuditAdminMixin, OperateButtonsMixin
from .models import Bill, BillTemplate


class TemplateNameFilter(admin.SimpleListFilter):
    title = "模板名称"  # ✅ 显示在右侧过滤栏的标题
    parameter_name = "template_name"  # ✅ URL 参数名（自己定义）

    def lookups(self, request, model_admin):
        """定义下拉选项"""
        return [(t.name, f"{t.template_code}:{t.name}") for t in BillTemplate.objects.all()]

    def queryset(self, request, queryset):
        """定义过滤逻辑"""
        if self.value():
            return queryset.filter(template__name=self.value())
        return queryset

@admin.register(Bill)
class BillAdmin(AdminBaseMixin, OperateButtonsMixin, AuditAdminMixin, admin.ModelAdmin):
    
    list_display = ("sn", "name", "template_name", "operate_buttons")
    readonly_fields = ("sn",)
    search_fields = ("sn", "name")
    list_filter = (TemplateNameFilter,)
    fields = ("name", "template", "params", "sn")
    
    operate_buttons_config = [
        {
            "name": "预览",
            "type": "text",
            "mode": "modal",
            "icon": "fa-solid fa-magnifying-glass",
            "modal_width": "46vw",
            "modal_height": "98vh",
            "url": lambda obj: reverse("preview_bill_pdf_view", kwargs={"id": obj.pk}),
        },
        {
            "name": "重新生成票据",
            "type": "text",
            "mode": "js",
            "icon": "el-icon-refresh",
            "js_func": "refresh_bill_pdf",
        }
    ]
    
    def template_name(self, obj):
        if hasattr(obj, "template"):
            return f"{obj.template.template_code}:{obj.template.name}"
        return "-"
    template_name.short_description = "模板"
    
    def get_list_display_links(self, request: HttpRequest, list_display):
        if request.user.is_superuser:
            return ("sn",)
        return None

    
    def has_delete_permission(self, request: HttpRequest, obj=None):
        return False
   



@admin.register(BillTemplate)
class UserAdmin(admin.ModelAdmin, OperateButtonsMixin):
    
    list_display = ("template_code", "name", "operate_buttons")
    list_display_links = ("template_code",)
    search_fields = ("template_code", "name")
    
    operate_buttons_config = [
        {
            "name": "预览",
            "type": "text",
            "mode": "modal",
            "icon": "fa-solid fa-magnifying-glass",
            "modal_width": "46vw",
            "modal_height": "98vh",
            "url": lambda obj: reverse("dynamic_rendering_bill_html_view", kwargs={"id": obj.pk}),
        }
    ]
    
    def has_delete_permission(self, request: HttpRequest, obj=None):
        return False
    

