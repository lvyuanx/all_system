import os
import uuid
from django.contrib import messages
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.utils.html import format_html
from django.utils.encoding import smart_str
from django.template.response import TemplateResponse
from django.http.response import HttpResponse

from bill.utils import pdf_util
from core.utils import admin_util
from .models import Bill, BillTemplate
from bill.utils import pdf_util

@admin.register(Bill)
class BillAdmin(admin_util.OperateButtonsMixin, admin_util.AuditAdminMixin, admin.ModelAdmin):
    
    list_display = ("name", "template_link", "operate_buttons")

    fields = ("name", "template", "params")
    
    operate_buttons_config = [
        {
            "name": "",
            "type": "text",
            "mode": "modal",
            "icon": "fa-solid fa-magnifying-glass",
            "modal_width": "35vw",
            "modal_height": "80vh",
            "url": lambda obj: reverse("preview_bill_pdf_view", kwargs={"id": obj.pk}),
        }
    ]
    
    def template_link(self, obj):
        if hasattr(obj, "template"):
            template = obj.template
            url = reverse("admin:bill_billtemplate_change", args=[template.pk])
            return format_html('<a href="{}">{}</a>', url, template.name)
        return "-"
    template_link.short_description = "模板"
   



@admin.register(BillTemplate)
class UserAdmin(admin.ModelAdmin):
    
    list_display = ("name",)
    

