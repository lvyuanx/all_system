#coding=utf-8
# -*- coding: UTF-8 -*-
import logging

from django.conf import settings

# class SqlFilter(logging.Filter):
#     """sql不进入日志文件"""
#     def filter(self, record):
#         record.ip = context_obj.ip
#         return record.name != '' or settings.DEBUG_SQL
    

# class RegisterParamsFilter(logging.Filter):
#     """sql不进入日志文件"""
#     def filter(self, record):
#         record.ip = getattr(context_obj, 'ip', '-')
#         return True