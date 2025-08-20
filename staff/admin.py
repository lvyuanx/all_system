from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Staff

from core.utils import admin_util

@admin.register(Staff)
class UserAdmin(admin.ModelAdmin):
    
    list_display = ("user_avatar", "staff_code", "fullname_link")

    def user_avatar(self, obj):
        avatar = obj.user.avatar
        if avatar:
            return admin_util.AdminListImagePreviewMixin.format_image_lightbox(avatar.url, "user_avatar")
        else:
            return ""
    user_avatar.short_description = "头像"
    
    def fullname_link(self, obj):
        if hasattr(obj, "user"):
            user = obj.user
            url = reverse("admin:core_auth_user_change", args=[user.pk])
            return format_html('<a href="{}">{}{}</a>', url, user.first_name, user.last_name)
        return "-"
    fullname_link.short_description = "姓名"
    
    list_display_links = ("staff_code",)
