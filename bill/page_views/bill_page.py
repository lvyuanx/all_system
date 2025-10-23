from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render

from bill.models import Bill, BillTemplate
from bill.utils import pdf_util
from core.utils import admin_util


def preview_bill_pdf_view(request, id: int):
    bill_manager = Bill.objects.filter(pk=id)
    if bill_manager.exists():
        obj = bill_manager.first()
        bill_path = obj.bill_path
        if not bill_path:
            # 调用工具生成 PDF
            media_path = pdf_util.jinja2_to_pdf(obj.template.content, obj.params)

            # 修改票据路径
            obj.bill_path = media_path
            obj.save()
            admin_util.log_custom_actions(request, [obj], "重新生成票据", 2)
        context = {
            "pdf_url": f"{settings.MEDIA_URL}{obj.bill_path}",  # 返回PDF的URL
        }
    else:
        context = {"pdf_url": ""}
    return render(request, "pdf/pdf_preview.html", context)


def dynamic_rendering_bill_html_view(request, id: int):
    bt_queryset = BillTemplate.objects.filter(pk=id)
    if not bt_queryset.exists():
        return Http404()
    bt = bt_queryset.first()
    return HttpResponse(bt.content)
