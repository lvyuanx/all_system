# -*-coding:utf-8 -*-

"""
# File       : staff_salary_basic_disbursement_list_view.py
# Time       : 2025-09-02 14:31:49
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询未发放工资信息
"""
from decimal import Decimal
from typing import Any, Dict, List
from django.db.models import Exists, OuterRef, F, QuerySet
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.utils import time_util
from staff.enums import StaffSalaryTypeChoices, StaffSalaryStatusChoices
from staff.models import Staff, StaffSalary
from .. import schemas


class Pagination(AsyncLimitOffsetPagination):
    async def aprocess_result(self, results):
        for item in results:
            basic_salary = item.get("basic_salary", Decimal("0.00"))
            account_balance = item.get("account_balance", Decimal("0.00"))
            max_salary = basic_salary
            actual_disbursement = basic_salary
            if account_balance < Decimal("0.00"):
                actual_disbursement = basic_salary + account_balance
                max_salary = actual_disbursement
            item["actual_disbursement"] = actual_disbursement
            item["max_salary"] = max_salary
        return results

    async def afilter_queryset(self, queryset: QuerySet[Staff, dict[str, Any]], input_filter: Dict):
        full_name = input_filter.get("full_name")
        if full_name:
            queryset = queryset.filter(user__full_name__contains=full_name)
        phone = input_filter.get("phone")
        if phone:
            queryset = queryset.filter(user__phone__contains=phone)
        return queryset


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "查询未发放工资信息失败"
    response_schema = schemas.BasicSalaryListItemSchema
    error_codes = []
    is_pagination = True
    pagination_class = Pagination

    @staticmethod
    async def api(request: HttpRequest):
        cur_time = time_util.now()
        year = cur_time.year
        month = cur_time.month
        return Staff.objects.filter(
            user__is_active=True,
        ).annotate(
            sid=F("id"),
            full_name=F("user__full_name"),
            phone=F("user__phone"),
            is_release_current_month=Exists(
                StaffSalary.objects.filter(
                    staff=OuterRef("pk"),
                    month=month,
                    year=year,
                    salary_type=StaffSalaryTypeChoices.BASIC_SALARY,
                ).exclude(status__in=[StaffSalaryStatusChoices.AUDIT_REJECT, StaffSalaryStatusChoices.CANCEL])
            ),
        ).filter(
            is_release_current_month=False
        ).values("sid", "basic_salary", "staff_code", "full_name", "phone", "account_balance")