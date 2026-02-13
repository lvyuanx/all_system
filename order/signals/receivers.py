# -*-coding:utf-8 -*-

"""
# File       : receivers.py
# Time       : 2025-09-04 20:54:43
# Author     : lyx
# version    : python 3.11
# Description: 信号监听器
"""
from decimal import Decimal
import logging
from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from staff.enums import (
    StaffSalaryTypeChoices,
    StaffIncomeExpenseChoices,
    OUT_SALSRY_ENUMS,
)
from core.utils import signal_util
from ..models import Order
from .signals import order_created_signal


logger = logging.getLogger("project")


@receiver(post_save, sender=Order)
@signal_util.safe_signal_handler
def order_post_save_signal_hendler(
    sender, instance: Order, created: bool, **kwargs
):
    if created:
        order_created_signal.send(sender=sender, instance=instance)
        

@receiver(order_created_signal, sender=Order)
@signal_util.safe_signal_handler
def order_created_signal_hendler(
    sender, instance: Order, **kwargs
):
    pass