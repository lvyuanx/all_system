# -*-coding:utf-8 -*-

"""
# File       : receivers.py
# Time       : 2025-09-04 20:54:43
# Author     : lyx
# version    : python 3.11
# Description: 信号监听器
"""
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.http import HttpRequest
from core.utils import signal_util

@receiver(user_logged_in)
@signal_util.safe_signal_handler
def my_handler(sender, request: HttpRequest, user, **kwargs):
    """
    Django 登录成功信号处理
    只在 admin 登录时设置一个标志，后续中间件会用这个标志写 cookie
    """
    if request.path.startswith('/admin/login/'):
        request.admin_login_success = True