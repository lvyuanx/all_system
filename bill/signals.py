# yourapp/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.utils import admin_util
from .models import Bill
from .utils import pdf_util

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Bill)
def handle_bill_save(sender, instance: Bill, created: bool, **kwargs):
    if not created:
        return

    content = instance.template.content
    params = instance.params
    media_path = pdf_util.jinja2_to_pdf(content, params)
    logger.debug(f"票据[{instance.id}]生成PDF成功，保存路径[{media_path}]")

    # 设置标志防止递归
    instance.bill_path = media_path
    instance.save(update_fields=['bill_path'])
