# -*-coding:utf-8 -*-
"""
# File       : staff_salary_hourly_batch_disbursement_view.py
# Time       : 2025-09-11 21:26:06
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 发放时薪工资
"""
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.db import transaction
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body, BusinessException
from core.utils import time_util
from staff.enums import StaffIncomeExpenseChoices, StaffSalaryTypeChoices
from staff.models import Staff, StaffSalary
from staff.utils import salary_util
from core.utils import admin_util, common_util
from .. import schemas

class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "发放时薪工资失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.BasicHourlyBatchDisbursementSchema = Body(...)
    ):
        
        batch_lst = []
        user = request.user
        year = data.year
        month = data.month
        # 在同步事务中同时生成流水号和插入工资
        def _create_salaries_and_sns():
            with transaction.atomic():
                # 批量生成流水号，并写入 SerialNumber 表
                serial_numbers = StaffSalary.get_sn(len(data.data))

                for idx, item in enumerate(data.data):
                    actual_disbursement = common_util.to_decimal(item.hourly_wage) * common_util.to_decimal(item.work_hours)
                    salary_data = {
                        "staff_id": item.sid,
                        "staff_code": item.staff_code,
                        "full_name": item.full_name,
                        "salary": actual_disbursement,
                        "income_expense": StaffIncomeExpenseChoices.INCOME,
                        "memo": item.memo,
                        "salary_type": StaffSalaryTypeChoices.HOURLY_SALARY,
                        "year": year,
                        "month": month,
                        "staff_hourly_wage": item.staff_hourly_wage,
                        "hourly_wage": item.hourly_wage,
                        "work_hours": item.work_hours,
                        "salary_serial_number": serial_numbers[idx],
                        "create_time": time_util.now(),
                        "create_user": user
                    }
                    salary_data["title"] = salary_util.generate_title(salary_data)
                    batch_lst.append(StaffSalary(**salary_data))

                # 批量创建工资流水
                StaffSalary.objects.bulk_create(batch_lst, batch_size=500)
                
                # 打印日志
                admin_util.log_custom_actions(request, batch_lst, "发放时薪工资成功", 1)

        await sync_to_async(_create_salaries_and_sns)()



