# -*-coding:utf-8 -*-

"""
# File       : signals.py
# Time       : 2025-09-04 20:53:55
# Author     : lyx
# version    : python 3.11
# Description: 信号定义
"""
from django.dispatch import Signal

image_lib_add_signal = Signal()
image_lib_del_signal = Signal()
