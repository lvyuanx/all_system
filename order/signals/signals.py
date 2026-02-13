# -*-coding:utf-8 -*-

"""
# File       : signals.py
# Time       : 2025-09-04 20:53:55
# Author     : lyx
# version    : python 3.11
# Description: 信号定义
"""
from django.dispatch import Signal

order_canceled_signal = Signal()
order_created_signal = Signal()
order_confirmed_signal = Signal()
order_scheduled_signal = Signal()
order_producing_signal = Signal()
order_finished_signal = Signal()
order_shipped_signal = Signal()
order_completed_signal = Signal()
