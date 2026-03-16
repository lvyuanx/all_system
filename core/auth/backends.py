# -*-coding:utf-8 -*-

"""
# File       : backends.py
# Description: 自定义认证后端，支持 用户名/手机号/工号 + 密码 登录
"""
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class MultiFieldAuthBackend(ModelBackend):
    """
    支持三种方式登录：
    - 用户名 (username)
    - 手机号 (phone)
    - 工号   (staff__staff_code)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        from django.contrib.auth import get_user_model
        UserModel = get_user_model()

        try:
            user = UserModel.objects.get(
                Q(username=username) |
                Q(phone=username) |
                Q(staff__staff_code=username)
            )
        except UserModel.DoesNotExist:
            # 防止时序攻击，仍执行一次密码哈希
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
