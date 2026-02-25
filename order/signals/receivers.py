# -*-coding:utf-8 -*-

"""
# File       : receivers.py
# Time       : 2025-09-04 20:54:43
# Author     : lyx
# version    : python 3.11
# Description: 信号监听器
"""
import logging
from django.db.models import F
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from staff.enums import (
    StaffSalaryTypeChoices,
    StaffIncomeExpenseChoices,
    OUT_SALSRY_ENUMS,
)
from core.utils import signal_util
from ..models import Order, OrderPayCa
from .signals import order_created_signal, order_canceled_signal, order_ship_singal, order_pay_signal, order_complete_signal
from client_mgmt.models import Client


logger = logging.getLogger("project")


@receiver(post_save, sender=Order)
@signal_util.safe_signal_handler
def order_post_save_signal_hendler(
    sender, instance: Order, created: bool, **kwargs
):
    if created:
        # 信号转发
        order_created_signal.send(sender=sender, instance=instance)
        

@receiver(order_created_signal, sender=Order)
@signal_util.safe_signal_handler
def order_created_signal_hendler(
    sender, instance: Order, **kwargs
):
    """订单创建成功"""
    receiver_phone = instance.receiver_phone
    client_manager = Client.objects.filter(client_phone=receiver_phone, is_active=True)
    if not client_manager.exists():
        raise Exception(f"客户[{receiver_phone}]不存在，请联系管理员手动处理！")
    
    client = client_manager.first()
    # 历史订单数量
    client.total_order_count += 1
    # 历史订单金额
    client.total_amount += instance.total_amount
    # 历史未付金额（创建订单的时候未支付）
    client.total_arrears += instance.payable_amount
    client.save()


@receiver(order_canceled_signal, sender=Order)
@signal_util.safe_signal_handler
def order_canceled_signal_hendler(
    sender, instance: Order, **kwargs
):
    """订单取消"""
    receiver_phone = instance.receiver_phone
    client_manager = Client.objects.filter(client_phone=receiver_phone, is_active=True)
    if not client_manager.exists():
        raise Exception(f"客户[{receiver_phone}]不存在, 请联系管理员手动处理！")

    client = client_manager.first()
    # 历史订单数量
    client.total_order_count -= 1
    # 历史订单金额
    client.total_amount -= instance.total_amount
    # 历史未付金额（创建订单的时候未支付）
    client.total_arrears -= instance.total_amount
    client.save()


@receiver(order_pay_signal, sender=OrderPayCa)
@signal_util.safe_signal_handler
def order_pay_signal_hendler(
    sender, instance: OrderPayCa, **kwargs
):
    """订单支付"""
    receiver_phone = instance.order.receiver_phone
    client_manager = Client.objects.filter(client_phone=receiver_phone, is_active=True)
    if not client_manager.exists():
        raise Exception(f"客户[{receiver_phone}]不存在, 请联系管理员手动处理！")

    client = client_manager.first()
    client.total_arrears -= instance.pay_amount
    client.save()


@receiver(order_ship_singal, sender=Order)
@signal_util.safe_signal_handler
def order_ship_singal_hendler(
    sender, instance: Order, **kwargs
):
    """订单发货"""
    receiver_phone = instance.receiver_phone
    client_manager = Client.objects.filter(client_phone=receiver_phone, is_active=True)
    if not client_manager.exists():
        raise Exception(f"客户[{receiver_phone}]不存在, 请联系管理员手动处理！")

    client = client_manager.first()

    if instance.shipping_fee > 0:
        client.total_amount += instance.shipping_fee
        client.total_arrears += instance.shipping_fee
    
    client.save()


@receiver(order_complete_signal, sender=Order)
@signal_util.safe_signal_handler
def order_complete_signal_hendler(
    sender, instance: Order, **kwargs
):
    """订单完成"""
    receiver_phone = instance.receiver_phone
    client_manager = Client.objects.filter(client_phone=receiver_phone, is_active=True)
    if not client_manager.exists():
        raise Exception(f"客户[{receiver_phone}]不存在, 请联系管理员手动处理！")

    client = client_manager.first()
    client.total_end_order_count += 1
    client.save()