# -*-coding:utf-8 -*-

"""
# File       : audit_admin_mixin.py
# Time       : 2025-09-08 10:29:04
# Author     : lyx
# version    : python 3.11
# Description: 审计字段自动处理
"""

class AuditAdminMixin:
    audit_exclude_fields = (
        "create_user",
        "create_time",
        "update_user",
        "update_time",
        "delete_user",
        "delete_time",
        "is_delete",
    )
    exclude_fields = tuple()

    def get_form(self, request, obj=None, **kwargs):
        """在form中去掉字段"""
        form = super().get_form(request, obj, **kwargs)
        for f in self.audit_exclude_fields:
            if f in form.base_fields:
                form.base_fields.pop(f)
        for f in self.exclude_fields:
            if f in form.base_fields:
                form.base_fields.pop(f)
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_delete=False)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.create_user = request.user
        else:
            obj.update_user = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        from django.utils import timezone

        obj.is_delete = True
        obj.delete_user = request.user
        obj.delete_time = timezone.now()
        obj.save()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)