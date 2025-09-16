# -*-coding:utf-8 -*-
"""
# File       : staff_salary_hourly_batch_disbursement_view.py
# Time       : 2025-09-11 21:26:06
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 发放时薪工资
"""
from asgiref.sync import sync_to_async
from django.db import transaction
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body, BusinessException
from core.utils import time_util
from staff.enums import StaffIncomeExpenseChoices, StaffSalaryTypeChoices
from staff.models import Staff, StaffSalary
from staff.utils import salary_util
from .. import schemas

class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "发放时薪工资失败"
    response_schema = None
    error_codes = [
        (
            "001",
            "员工{full_name}本月可发放基础工资在0~{max_salary}之间, 但是却发放了{salary}元, 发放失败!",
        ),
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: list[schemas.HourlyStaffSalaryListItemSchema] = Body(...)
    ):
        now = time_util.now()
        sids = [item.sid for item in data]

        # 获取员工信息
        staff_arr = await sync_to_async(list)(
            Staff.objects.filter(pk__in=sids).values(
                "id", "account_balance", "basic_salary"
            )
        )
        staff_max_salary_dict = {
            item["id"]: (
                item["basic_salary"]
                if item["account_balance"] > 0
                else item["basic_salary"] + item["account_balance"]
            )
            for item in staff_arr
        }

        batch_lst = []
        user = request.user
        # 在同步事务中同时生成流水号和插入工资
        def _create_salaries_and_sns():
            with transaction.atomic():
                # 批量生成流水号，并写入 SerialNumber 表
                serial_numbers = StaffSalary.get_sn(len(data))

                for idx, item in enumerate(data):
                    max_salary = staff_max_salary_dict.get(item.sid)
                    if item.actual_disbursement < 0 or item.actual_disbursement > max_salary:
                        raise BusinessException(
                            "001",
                            {
                                "full_name": item.full_name,
                                "max_salary": max_salary,
                                "salary": item.actual_disbursement,
                            },
                        )

                    salary_data = {
                        "staff_id": item.sid,
                        "staff_code": item.staff_code,
                        "full_name": item.full_name,
                        "salary": item.actual_disbursement,
                        "income_expense": StaffIncomeExpenseChoices.INCOME,
                        "memo": item.memo,
                        "salary_type": StaffSalaryTypeChoices.BASIC_SALARY,
                        "year": now.year,
                        "month": now.month,
                        "basic_salary": item.basic_salary,
                        "salary_serial_number": serial_numbers[idx],
                        "create_time": now,
                        "create_user": user
                    }
                    salary_data["title"] = salary_util.generate_title(salary_data)
                    batch_lst.append(StaffSalary(**salary_data))

                # 批量创建工资流水
                StaffSalary.objects.bulk_create(batch_lst, batch_size=500)

        await sync_to_async(_create_salaries_and_sns)()



