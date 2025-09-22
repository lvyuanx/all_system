# -*-coding:utf-8 -*-
"""
# File       : staff_salary_batch_disbursement_view.py
# Time       : 2025-09-11 21:26:06
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 发放工资
"""
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.db import transaction
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body, BusinessException
from core.utils import time_util
from staff.enums import StaffIncomeExpenseChoices, OUT_SALSRY_ENUMS, StaffSalaryTypeChoices
from staff.models import Staff, StaffSalary
from staff.utils import salary_util
from core.utils import admin_util
from .. import schemas

class View(BaseApi):
    api_status = BaseApi.ApiStatus.ARCHIVED
    methods = ["POST"]
    finally_code = "000", "发放工资失败"
    response_schema = None
    error_codes = [
        ("001", "工资发放类型错误")
    ]

    @staticmethod
    async def api(
        request: HttpRequest, data: schemas.SalaryBatchDisbursementSchema = Body(...)
    ):
        
        batch_lst = []
        user = request.user
        salary_type = StaffSalaryTypeChoices(data.salary_type)
        if salary_type in OUT_SALSRY_ENUMS:
            raise BusinessException("001")
        # 在同步事务中同时生成流水号和插入工资
        def _create_salaries_and_sns():
            with transaction.atomic():
                # 批量生成流水号，并写入 SerialNumber 表
                serial_numbers = StaffSalary.get_sn(len(data.data))
                for idx, item in enumerate(data.data):
                    disbursement_time = item.disbursement_time
                    salary_data = {
                        "staff_id": item.sid,
                        "staff_code": item.staff_code,
                        "full_name": item.full_name,
                        "salary": item.actual_disbursement,
                        "income_expense": StaffIncomeExpenseChoices.INCOME,
                        "memo": item.memo,
                        "salary_type": salary_type,
                        "year": disbursement_time.year,
                        "month": disbursement_time.month,
                        "day": disbursement_time.day,
                        "salary_serial_number": serial_numbers[idx],
                        "create_time": time_util.now(),
                        "create_user": user
                    }
                    salary_data["title"] = salary_util.generate_title(salary_data)
                    batch_lst.append(StaffSalary(**salary_data))

                # 批量创建工资流水
                StaffSalary.objects.bulk_create(batch_lst, batch_size=500)
                
                # 打印日志
                admin_util.log_custom_actions(request, batch_lst, f"发放{salary_type.label}成功", 1)

        await sync_to_async(_create_salaries_and_sns)()



