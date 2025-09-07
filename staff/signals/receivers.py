# -*-coding:utf-8 -*-

"""
# File       : receivers.py
# Time       : 2025-09-04 20:54:43
# Author     : lyx
# version    : python 3.11
# Description: 信号监听器
"""
from decimal import Decimal
import logging
from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from staff.enums import (
    StaffSalaryTypeChoices,
    StaffIncomeExpenseChoices,
    OUT_SALSRY_ENUMS,
)
from core.utils import signal_util
from .signals import after_salary_audit_pass_signal
from ..models import Staff, StaffSalary
from ..utils import salary_util

logger = logging.getLogger("project")


@receiver(post_save, sender=StaffSalary)
@signal_util.safe_signal_handler
def staff_salary_save_signal_hendler(
    sender, instance: StaffSalary, created: bool, **kwargs
):
    if created:
        # 创建工资的时候触发
        staff = instance.staff

        # 定义收支类型
        income_expense = (
            StaffIncomeExpenseChoices.EXPENSE
            if instance.salary_type in OUT_SALSRY_ENUMS
            else StaffIncomeExpenseChoices.INCOME
        )
        data = {
            "staff_code": staff.staff_code,
            "full_name": staff.user.full_name,
            "phone": staff.user.phone,
            "income_expense": income_expense,
        }
        instance.income_expense = income_expense

        # 时薪工资，会根据时薪和工作时间计算，如果表单上填写了总额会被覆盖掉
        if instance.salary_type == StaffSalaryTypeChoices.HOURLY_SALARY:
            data["salary"] = instance.hourly_wage * instance.work_hours
            data["staff_hourly_wage"] = staff.hourly_wage
            instance.salary = data["salary"]
            instance.staff_hourly_wage = data["staff_hourly_wage"]

        # 基础工资会保存当前时刻员工的基础工资
        if instance.salary_type == StaffSalaryTypeChoices.BASIC_SALARY:
            data["basic_salary"] = staff.basic_salary
            instance.basic_salary = data["basic_salary"]

        # 如果是支出类型的工资，会设置为未发放（方便页面url过滤）
        if instance.income_expense == StaffIncomeExpenseChoices.EXPENSE:
            data["is_release"] = False
            instance.is_release = False

        # 封装好信息后，生产title
        instance.staff_code = data["staff_code"]
        instance.full_name = data["full_name"]
        instance.phone = data["phone"]
        instance.income_expense = income_expense
        data["title"] = salary_util.generate_title(instance)
    else:
        # 编辑工资信息触发
        data = {}

        # 编辑工资信息，会重新计算时薪工资
        if instance.salary_type == StaffSalaryTypeChoices.HOURLY_SALARY:
            salary = instance.hourly_wage * instance.work_hours
            if instance.salary != salary:
                data["salary"] = salary
                instance.salary = data["salary"]
                data["title"] = salary_util.generate_title(instance)
    if data:  # 只有当特定数据改变才会触发修改
        StaffSalary.objects.filter(pk=instance.pk).update(**data)


@receiver(after_salary_audit_pass_signal, sender=StaffSalary)
@signal_util.safe_signal_handler
def after_salary_audit_pass_signal_handler(sender, instance: StaffSalary, **kwargs):
    """
    收入/支出审核通过后，更新员工工资相关字段。
    使用 F() 表达式保证原子性，避免并发问题。
    """
    staff = instance.staff
    # 确保 salary 是 Decimal
    salary = Decimal(instance.salary)

    with transaction.atomic():
        if instance.income_expense == StaffIncomeExpenseChoices.INCOME:  # 收入
            Staff.objects.filter(pk=staff.pk).update(
                total_salary=F('total_salary') + salary,
                pending_salary=F('pending_salary') + salary
            )
        else:  # 支出
            Staff.objects.filter(pk=staff.pk).update(
                pending_salary=F('pending_salary') - salary,
                paid_salary=F('paid_salary') + salary
            )