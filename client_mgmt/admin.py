from django.contrib import admin
from django.http import HttpRequest

from core.admin_extra import AdminBaseMixin
from core.admin_extra.forms import AdminFormImageUploadForm
from core.admin_extra.mixins import AdminListImagePreviewMixin
from .models import Client


@admin.register(Client)
class UserAdmin(AdminBaseMixin, AdminListImagePreviewMixin, admin.ModelAdmin):

    class UserAdminForm(AdminFormImageUploadForm):
        upload_image_fields = ("company_logo",)

        class Meta:
            model = Client
            fields = "__all__"

    form = UserAdminForm
    image_preview = {"company_logo": "头像"}
    list_display = (
        "company_logo_preview",
        "client_name",
        "client_phone",
        "client_sex",
        "company_name",
        "company_address",
        "unfinished_order_total",
        "is_active",
    )
    list_filter = ("company_name",)
    search_fields = ("client_name", "client_phone")
    readonly_fields = ("total_amount", "total_arrears", "total_order_count", "total_end_order_count")
    list_display_links = []
    sortable_by = ("client_name",)
    
    @admin.display(description="未结束订单数")
    def unfinished_order_total(self, obj):
        return obj.total_order_count - obj.total_end_order_count
    
    
    def get_list_display_links(self, request: HttpRequest, list_display):
        if request.user.is_superuser:
            return ("client_name",)
        return self.list_display



