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
class BillAdmin(admin_util.OperateBtnAdminMixin, admin.ModelAdmin):
    
    list_display = ("name", "template_link", "operator_buttons")

    fields = ("name", "template", "params")
    
    def template_link(self, obj):
        if hasattr(obj, "template"):
            template = obj.template
            url = reverse("admin:bill_billtemplate_change", args=[template.pk])
            return format_html('<a href="{}">{}</a>', url, template.name)
        return "-"
    template_link.short_description = "模板"
    
    operate_btn_dict = {
        "generate_pdf_button": {
            "name": "重新生成票据",
            "type": "primary",
            "confirm": {"text": "确定要重新生成票据吗？"},
            "onclick": lambda self, request, obj: self._generate_pdf(request, obj),
        },
        "view_pdf": {
            "name": "预览",
            "type": "primary",
            "mode": "modal",  # 也可以改为 "normal"
            "modal_width": "650px",
            "modal_height": "700px",
            "onclick":  lambda self, request, obj: self._view_pdf(request, obj),
        },
    }
    
    def _view_pdf(self, request, obj):
        # obj 是当前模型实例
        bill_path = obj.bill_path
        if not bill_path:
            # 调用工具生成 PDF
            media_path = pdf_util.jinja2_to_pdf(obj.template.content, obj.params)

            # 修改票据路径
            obj.bill_path = media_path
            obj.save()
            admin_util.log_custom_action(request, obj, "重新生成票据")
        context = {
            "pdf_url": f"{settings.MEDIA_URL}{obj.bill_path}",  # 返回PDF的URL
        }
        return TemplateResponse(request, "pdf/pdf_preview.html", context)

    def _generate_pdf(self, request, obj: Bill):
        try:
            # 调用工具生成 PDF
            media_path = pdf_util.jinja2_to_pdf(obj.template.content, obj.params)

            # 修改票据路径
            obj.bill_path = media_path
            obj.save()
            admin_util.log_custom_action(request, obj, "重新生成票据")

            filename = os.path.basename(media_path)

            # 构造媒体 URL，用于前端访问
            pdf_url = os.path.join(settings.MEDIA_URL, media_path).replace("\\", "/")
            self.message_user(
                request,
                f"✅ 文件已生成：<a href='{pdf_url}' target='_blank'>{smart_str(filename)}</a>",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(request, f"生成失败: {e}", level=messages.ERROR)
        return redirect(request.META.get("HTTP_REFERER", ".."))
    
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新增时
            if hasattr(obj, 'create_user'):
                obj.create_user = request.user
        else:  # 修改时
            if hasattr(obj, 'update_user'):
                obj.update_user = request.user
        super().save_model(request, obj, form, change)


   

    



@admin.register(BillTemplate)
class UserAdmin(admin.ModelAdmin):
    
    list_display = ("name",)
    

