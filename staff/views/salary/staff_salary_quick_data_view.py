# -*-coding:utf-8 -*-

"""
# File       : staff_salary_quick_data_view.py
# Time       : 2026-02-27 21:20:08
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 工资快捷页面数据查询
"""
import datetime
from typing import Optional
from asgiref.sync import sync_to_async
import asyncio
from django.db.models import F, IntegerField, ExpressionWrapper
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.utils import time_util
from site_mgmt.utils import site_util
from staff.enums import StaffIncomeExpenseChoices, StaffSalaryStatusChoices, StaffSalaryTypeChoices
from django.db.models import QuerySet
from .. import schemas
from staff.models import Staff, StaffSalary

async def get_wait_distribution_basic_count(ss_manager: QuerySet[StaffSalary]): 
    nowstr = time_util.now_str("%Y-%m-%d")
    year, month, _ = nowstr.split("-")
    
    salary_staff_ids = ss_manager.filter(
        salary_type=StaffSalaryTypeChoices.BASIC_SALARY,
        year=year,
        month=month,
        status=StaffSalaryStatusChoices.AUDIT_PASS,
    ).values_list("staff_id", flat=True)

    staff_ids = Staff.objects.filter(
        user__is_active=True,
    ).values_list("id", flat=True)
    
    staff_ids = list(set([item async for item in staff_ids]) - set([item async for item in salary_staff_ids]))
    
    return len(staff_ids)

async def get_wait_audit_count(ss_manager: QuerySet[StaffSalary]):
    ss_manager.filter(
        status__in=[StaffSalaryStatusChoices.UNAUDIT, StaffSalaryStatusChoices.CORRECTIONED],
    )
    return await ss_manager.acount()


async def get_wait_release_count(ss_manager: QuerySet[StaffSalary]):
    ss_manager.filter(
        status=StaffSalaryStatusChoices.AUDIT_PASS,
        income_expense=StaffIncomeExpenseChoices.EXPENSE,
    )
    return await ss_manager.acount()

async def get_wait_correction_count(ss_manager: QuerySet[StaffSalary]):
    ss_manager.filter(
        status=StaffSalaryStatusChoices.PENDING_CORRECTION,
    )
    return await ss_manager.acount()


def datetime_split(d: datetime) -> tuple[int, int, int]:
    day_str = time_util.datetime_to_str(d, "%Y-%m-%d")
    return day_str.split("-")
    

async def get_salary(ss_manager: QuerySet[StaffSalary], data: Optional[schemas.SalaryQuickDataReqSchema] = None):
    """
    获取指定时间段的工资汇总
    """

    if data and data.start and data.end:
        start_year, start_month, start_day = datetime_split(data.start)
        end_year, end_month, end_day = datetime_split(data.end)

        # 将年月日组合成整数 YYYYMMDD，用于跨月跨年正确筛选
        start_int = int(start_year) * 10000 + int(start_month) * 100 + int(start_day)
        end_int = int(end_year) * 10000 + int(end_month) * 100 + int(end_day)

        date_expr = ExpressionWrapper(
            F("year") * 10000 + F("month") * 100 + F("day"),
            output_field=IntegerField()
        )

        ss_manager = ss_manager.annotate(ymd=date_expr).filter(ymd__range=(start_int, end_int))
    else:
        today = time_util.now().date()
        first_day = today.replace(day=1)
        ss_manager = ss_manager.filter(year=first_day.year, month=first_day.month)

    # 筛选审核通过的收入类型
    salary_lst = ss_manager.filter(
        status=StaffSalaryStatusChoices.AUDIT_PASS,
        income_expense=StaffIncomeExpenseChoices.INCOME,
    ).values("salary", "salary_type")

    # 初始化结果字典
    rst = {
        "basic_salary": 0,
        "overtime_salary": 0,
        "bonus_salary": 0,
        "hourly_salary": 0,
        "performance_evaluation_salary": 0,
        "commission_salary": 0,
        "other_salary": 0,
    }

    # 异步遍历查询结果
    async for item in salary_lst:
        salary_type = item.get("salary_type")
        salary_value = item.get("salary") or 0

        if salary_type == StaffSalaryTypeChoices.BASIC_SALARY:
            rst["basic_salary"] += salary_value
        elif salary_type == StaffSalaryTypeChoices.OVERTIME_SALARY:
            rst["overtime_salary"] += salary_value
        elif salary_type == StaffSalaryTypeChoices.BONUS:
            rst["bonus_salary"] += salary_value
        elif salary_type == StaffSalaryTypeChoices.HOURLY_SALARY:
            rst["hourly_salary"] += salary_value
        elif salary_type == StaffSalaryTypeChoices.PERFORMANCE_EVALUATION:
            rst["performance_evaluation_salary"] += salary_value
        elif salary_type == StaffSalaryTypeChoices.COMMISSION:
            rst["commission_salary"] += salary_value
        elif salary_type == StaffSalaryTypeChoices.OTHER:
            rst["other_salary"] += salary_value

    return rst
        

class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "工资快捷页面数据查询失败"
    response_schema = schemas.SalaryQuickDataSchema
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest, data: schemas.SalaryQuickDataReqSchema | None = Body(default=None, description="查询参数")):
        sites = await sync_to_async(site_util.get_cur_sites)(request)
        ss_manager = StaffSalary.objects.filter(
            is_delete=False,
            staff__site__in=sites
        )

        get_wait_distribution_basic_count_task = asyncio.create_task(get_wait_distribution_basic_count(ss_manager))
        get_wait_audit_count_task = asyncio.create_task(get_wait_audit_count(ss_manager))
        get_wait_correction_count_task = asyncio.create_task(get_wait_correction_count(ss_manager))
        get_wait_release_count_task = asyncio.create_task(get_wait_release_count(ss_manager))
        get_salary_task = asyncio.create_task(get_salary(ss_manager, data))
        
        await asyncio.gather(
            get_wait_distribution_basic_count_task,
            get_wait_audit_count_task,
            get_wait_correction_count_task,
            get_wait_release_count_task,
            get_salary_task
        )
        
        rlt = {
            "wait_audit_count": get_wait_audit_count_task.result(),
            "wait_correction_count": get_wait_correction_count_task.result(),
            "wait_distribution_basic_count": get_wait_distribution_basic_count_task.result(),
            "wait_release_count": get_wait_release_count_task.result(),
        }
        rlt.update(
            get_salary_task.result()
        )
        return rlt