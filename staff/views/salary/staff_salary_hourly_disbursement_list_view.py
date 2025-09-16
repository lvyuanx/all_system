# -*-coding:utf-8 -*-

"""
# File       : staff_salary_hourly_disbursement_list_view.py
# Time       : 2025-09-02 14:31:49
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询未发放时薪工资信息
"""
from decimal import Decimal
from typing import Any, Dict
from django.db.models import Exists, OuterRef, F, QuerySet
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination
from core.utils import time_util
from staff.enums import StaffSalaryTypeChoices, StaffSalaryStatusChoices
from staff.models import Staff, StaffSalary
from .. import schemas


class Pagination(AsyncLimitOffsetPagination):
    async def aprocess_result(self, results):
        """
        在分页结果返回前，对每一条数据做二次加工
        """
        for item in results:
            account_balance = item.get("account_balance", Decimal("0.00"))
            staff_hourly_wage = item.get("hourly_wage", Decimal("0.00"))

            hourly_wage = staff_hourly_wage
            work_hours = 0

            if account_balance < Decimal("0.00"):
                actual_disbursement = account_balance
            else:
                actual_disbursement = Decimal("0.00")

            item["actual_disbursement"] = actual_disbursement
            item["staff_hourly_wage"] = staff_hourly_wage
            item["work_hours"] = work_hours
            item["hourly_wage"] = hourly_wage
        return results

    async def afilter_queryset(self, queryset: QuerySet[Staff, Dict[str, Any]], input_filter: Dict):
        """
        按前端传入的 filter 字典筛选
        """
        # 基础条件
        full_name = input_filter.get("full_name")
        if full_name:
            queryset = queryset.filter(user__full_name__contains=full_name)

        phone = input_filter.get("phone")
        if phone:
            queryset = queryset.filter(user__phone__contains=phone)

        # 年月条件
        month_str = input_filter.get("month")
        if month_str:
            month_datetime = time_util.str_to_datetime(month_str, "%Y-%m")
            year = month_datetime.year
            month = month_datetime.month
        else:
            now = time_util.now()
            last_month = time_util.last_month(now)
            year = last_month.year
            month = last_month.month

        # 标记是否已经发放过当月工资
        queryset = queryset.annotate(
            is_release_current_month=Exists(
                StaffSalary.objects.filter(
                    staff=OuterRef("pk"),
                    month=month,
                    year=year,
                    salary_type=StaffSalaryTypeChoices.HOURLY_SALARY,
                ).exclude(
                    status__in=[
                        StaffSalaryStatusChoices.AUDIT_REJECT,
                        StaffSalaryStatusChoices.CANCEL,
                    ]
                )
            )
        ).filter(is_release_current_month=False)

        return queryset


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "查询未发放时薪信息失败"
    response_schema = schemas.HourlyStaffSalaryListItemSchema
    error_codes = []
    is_pagination = True
    pagination_class = Pagination

    @staticmethod
    async def api(request: HttpRequest):
        """
        API 入口，初始查询所有在职员工
        """
        return Staff.objects.filter(
            user__is_active=True,
        ).annotate(
            sid=F("id"),
            full_name=F("user__full_name"),
            phone=F("user__phone"),
        ).values(
            "sid",
            "hourly_wage",
            "staff_code",
            "full_name",
            "phone",
            "account_balance",
        )
