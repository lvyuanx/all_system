# -*-coding:utf-8 -*-

"""
# File       : perm.py
# Time       : 2025-08-12 09:38:30
# Author     : lyx
# version    : python 3.11
# Description: auth 模块权限定义枚举
"""
from enum import StrEnum
from core.utils import model_util


class UserPrem(StrEnum):

    后台管理员 = "ADMIN_MANAGE"
    财务 = "FINANCE"
    员工 = "STAFF"


    

