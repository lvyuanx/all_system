# -*-coding:utf-8 -*-

"""
# File       : signals.py
# Time       : 2025-09-04 20:53:55
# Author     : lyx
# version    : python 3.11
# Description: 信号定义
"""
from django.dispatch import Signal

# 工资审批通过后
after_salary_audit_pass_signal = Signal()
