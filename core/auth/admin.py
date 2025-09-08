from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Permission, Group
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.html import format_html_join
from django.shortcuts import redirect

from core.admin_extra import AdminBaseMixin
from core.admin_extra.mixins import AdminListImagePreviewMixin
from core.admin_extra.forms import AdminFormImageUploadForm
from core.conf import settings
from core.utils import admin_util
from .models import User, SimpleuiMenus


@admin.register(User)
class UserAdmin(AdminBaseMixin, AdminListImagePreviewMixin, admin.ModelAdmin):

    class UserAdminForm(AdminFormImageUploadForm):
        upload_image_fields = ("avatar",)

        class Meta:
            model = User
            fields = "__all__"

    form = UserAdminForm

    """列表中图片预览字段"""
    image_preview = {"avatar": "头像"}
    # 定制哪些字段需要展示
    list_display = (
        "avatar_preview",
        "staff_code_link",
        "username",
        "full_name",
        "email",
        "is_superuser",
        "is_active",
        "last_login",
        "phone",
    )

    def staff_code_link(self, obj):
        if hasattr(obj, "staff"):
            staff = obj.staff
            url = reverse("admin:staff_staff_change", args=[staff.pk])
            return format_html('<a href="{}">{}</a>', url, staff.staff_code)
        return "-"

    staff_code_link.short_description = "工号"

    """编辑页分组展示用户信息"""
    fieldsets = (
        (
            "基本信息",
            {
                "fields": (
                    "avatar",
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "sex",
                    "age",
                )
            },
        ),
        (
            "权限信息",
            {
                "fields": ("is_superuser", "is_staff", "is_active", "groups"),
            },
        ),
    )

    list_display_links = ("username",)

    """排序字段"""
    sortable_by = ("username", "last_login")

    """定义哪个字段可以编辑"""
    list_editable = ("is_active",)

    """过滤选项"""
    list_filter = (
        "is_superuser",
        "is_active",
    )


    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "user_permissions":
            kwargs["queryset"] = Permission.objects.filter(
                content_type__app_label="core_auth", content_type__model="user"
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    """搜索框 ^, =, @, None=icontains"""
    search_fields = ["username", "phone"]

    operate_btn_dict = {
        "resertPwd": {
            "name": "重置密码",
            "type": "primary",
            "confirm": {"text": "确定将密码重置为初始密码码？"},
            "onclick": lambda self, request, obj: self.resert_pwd(request, obj),
        }
    }

    def resert_pwd(self, request: HttpRequest, obj: User):
        try:
            if request.user.pk == obj.pk:
                self.message_user(
                    request,
                    f"密码重置失败，请在个人中心中修改自己的密码！",
                    level=messages.ERROR,
                )
            else:
                obj.password = settings.DEFAULT_PASSWORD
                obj.save()
                admin_util.log_custom_action(
                    request, obj, f"用户{obj.username}重置密码成功"
                )
        except Exception as e:
            self.message_user(request, f"生成失败: {e}", level=messages.ERROR)
        return redirect(request.META.get("HTTP_REFERER", ".."))


@admin.register(SimpleuiMenus)
class UserAdmin(AdminBaseMixin, admin.ModelAdmin):
    list_display = ("name", "url", "is_active")
    list_display_links = ("name",)
    """排序字段"""
    sortable_by = ("name",)

    """定义哪个字段可以编辑"""
    list_editable = ("is_active",)


admin.site.unregister(Group)
@admin.register(Group)
class GroupAdmin(AdminBaseMixin, admin.ModelAdmin):
    """分组管理"""

    list_display = ("name", "tagged_permissions")

    def tagged_permissions(self, obj):
        packs = obj.permission_packs.all()
        if not packs:
            return "-"
        return format_html_join(
            "",
            '<span style="display:inline-block; background:#f0f9eb; color:#67c23a; '
            'border:1px solid #e1f3d8; border-radius:4px; padding:2px 8px; margin:2px; font-size:12px;">{}</span>',
            ((f"{p.pack_name}",) for p in packs),
        )

    tagged_permissions.short_description = "权限标签"

    actions = ["blank_delete"]  # 只保留你自定义的操作


Group._meta.verbose_name = "角色组"
Group._meta.verbose_name_plural = "用户组管理"


admin.site.site_header = "管理系统"
admin.site.site_title = "管理系统"
admin.site.index_title = "3"
