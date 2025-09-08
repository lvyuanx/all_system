# -*-coding:utf-8 -*-

"""
# File       : create_time_quick_mixin.py
# Time       : 2025-09-08 10:32:56
# Author     : lyx
# version    : python 3.11
# Description: 快捷时间过滤器，继承后可重写lookups方法
"""
from datetime import datetime, time, timedelta
from django.contrib import admin

from core.utils import time_util

class CreateTimeQuickFilter(admin.SimpleListFilter):
    title = "创建时间(快捷)"
    parameter_name = "create_time_quick"

    def lookups(self, request, model_admin):
        return (
            ("last_month", "上个月"),
            ("this_month", "本月"),
            ("half_year", "半年内"),
            ("this_year", "今年"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if not v:
            return queryset

        now = time_util.now()  # tz-aware datetime
        today = now.date()  # 当前日期 (date)

        if v == "last_month":
            # 上个月第一天
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1).date()
                end_date = datetime(today.year, 1, 1).date()
            else:
                start_date = datetime(today.year, today.month - 1, 1).date()
                end_date = datetime(today.year, today.month, 1).date()

        elif v == "this_month":
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1).date()
            else:
                end_date = datetime(today.year, today.month + 1, 1).date()

        elif v == "half_year":
            start_date = today - timedelta(days=182)  # 半年前
            end_date = today + timedelta(days=1)

        elif v == "this_year":
            start_date = datetime(today.year, 1, 1).date()
            end_date = datetime(today.year + 1, 1, 1).date()
        else:
            return queryset

        # 转换为 tz-aware datetime，保持和 now 的 tz 一致
        start = datetime.combine(start_date, time.min, tzinfo=now.tzinfo)
        end = datetime.combine(end_date, time.min, tzinfo=now.tzinfo)

        return queryset.filter(create_time__gte=start, create_time__lt=end)