# -*-coding:utf-8 -*-
"""
# File       : staff_salary_basic_batch_disbursement_view.py
# Time       : 2025-09-11 21:26:06
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 发放基础工资
"""
from asgiref.sync import sync_to_async
from django.db import transaction
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.utils import admin_util, time_util
from staff.enums import StaffIncomeExpenseChoices, StaffSalaryTypeChoices
from staff.models import StaffSalary
from staff.utils import salary_util
from .. import schemas

class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "发放基础工资失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.BasicSalaryBatchDisbursementSchema = Body(...)
    ):
        year = data.year
        month = data.month
        user = request.user
        batch_lst = []
        # 在同步事务中同时生成流水号和插入工资
        def _create_salaries_and_sns():
            with transaction.atomic():
                # 批量生成流水号，并写入 SerialNumber 表
                serial_numbers = StaffSalary.get_sn(len(data.data))

                for idx, item in enumerate(data.data):

                    salary_data = {
                        "staff_id": item.sid,
                        "staff_code": item.staff_code,
                        "full_name": item.full_name,
                        "salary": item.actual_disbursement,
                        "income_expense": StaffIncomeExpenseChoices.INCOME,
                        "memo": item.memo,
                        "salary_type": StaffSalaryTypeChoices.BASIC_SALARY,
                        "year": year,
                        "month": month,
                        "basic_salary": item.basic_salary,
                        "salary_serial_number": serial_numbers[idx],
                        "create_time": time_util.now(),
                        "create_user": user
                    }
                    salary_data["title"] = salary_util.generate_title(salary_data)
                    batch_lst.append(StaffSalary(**salary_data))

                # 打印日志
                admin_util.log_custom_actions(request, batch_lst, "发放基础工资成功", 1)

                # 批量创建工资流水
                StaffSalary.objects.bulk_create(batch_lst, batch_size=500)
                

        await sync_to_async(_create_salaries_and_sns)()



