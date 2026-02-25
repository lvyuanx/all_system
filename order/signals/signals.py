# -*-coding:utf-8 -*-

"""
# File       : signals.py
# Time       : 2025-09-04 20:53:55
# Author     : lyx
# version    : python 3.11
# Description: 信号定义
"""
from django.dispatch import Signal

# 订单取消
order_canceled_signal = Signal()

# 订单创建
order_created_signal = Signal()

# 订单发货
order_ship_singal = Signal()

# 订单支付
order_pay_signal = Signal()

# 订单完成
order_complete_signal = Signal()
