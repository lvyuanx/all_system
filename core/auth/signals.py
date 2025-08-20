from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.http import HttpRequest

@receiver(user_logged_in)
def my_handler(sender, request: HttpRequest, user, **kwargs):
    """
    Django 登录成功信号处理
    只在 admin 登录时设置一个标志，后续中间件会用这个标志写 cookie
    """
    if request.path.startswith('/admin/login/'):
        request.admin_login_success = True
