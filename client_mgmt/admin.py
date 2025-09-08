from django.contrib import admin

from core.admin_extra.forms import AdminFormImageUploadForm
from core.admin_extra.mixins import AdminListImagePreviewMixin
from .models import Client


@admin.register(Client)
class UserAdmin(AdminListImagePreviewMixin, admin.ModelAdmin):

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
        "company_address",
        "is_active",
    )
    list_display_links = ("client_name",)
    """排序字段"""
    sortable_by = ("client_name",)

    """定义哪个字段可以编辑"""
    list_editable = ("is_active",)

    """分页：每页10条"""
    list_per_page = 10

    """最大条目"""
    list_max_show_all = 200  # default

    """按日期分组"""
    # date_hierarchy = "last_login"

    """默认空值"""
    empty_value_display = ""
