# -*-coding:utf-8 -*-

"""
# File       : staff_salary_basic_disbursement_view.py
# Time       : 2025-09-02 14:31:49
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询未发放工资信息
"""

from decimal import Decimal
from typing import List
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from .. import schemas


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询未发放工资信息失败"
    response_schema = List[schemas.BasicSalaryListItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return [
            schemas.BasicSalaryListItemSchema(
                staff_code="A01",
                full_name="张三",
                phone="12345678901",
                basic_salary=Decimal("1000.00"),
                actual_disbursement=Decimal("1000.00"),
                memo="无"
            )
        ]