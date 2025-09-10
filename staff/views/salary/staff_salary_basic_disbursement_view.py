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
from core.ninja_extra.base_pagination import AsyncCustomLimitOffsetPagination
from staff.models import StaffSalary
from ninja.pagination import paginate
from .. import schemas


class Pagination(AsyncCustomLimitOffsetPagination):
    def process_queryset(self, results):
        return results


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询未发放工资信息失败"
    response_schema = schemas.BasicSalaryListItemSchema
    error_codes = []
    pagination_class = Pagination

    @staticmethod
    async def api(request: HttpRequest):
        return StaffSalary.objects.all()