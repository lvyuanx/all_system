# -*-coding:utf-8 -*-

"""
# File       : receivers.py
# Time       : 2025-09-04 20:54:43
# Author     : lyx
# version    : python 3.11
# Description: 信号监听器
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.utils import admin_util
from ..models import Bill
from ..utils import pdf_util

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Bill)
def handle_bill_save(sender, instance: Bill, created: bool, **kwargs):
    template_content = instance.template.content
    params = instance.params
    media_path = pdf_util.jinja2_to_pdf(template_content, params)
    logger.debug(f"票据[{instance.id}]生成PDF成功，保存路径[{media_path}]")
    Bill.objects.filter(id=instance.id).update(bill_path=media_path)
