from django.db import models


class StaffIncomeExpenseChoices(models.IntegerChoices):
    INCOME = 1, "收入"
    EXPENSE = 2, "支出"


class StaffSalaryStatusChoices(models.IntegerChoices):
    UNAUDIT = 1, "未审核"
    AUDIT_PASS = 2, "审核通过"
    PENDING_CORRECTION = 3, "待修正"
    CORRECTIONED = 4, "已修正"
    AUDIT_REJECT = 5, "审核拒绝"
    CANCEL = 6, "取消"
        


class StaffSalaryTypeChoices(models.IntegerChoices):
    ADVANCE_PAYMENT = 1, "预支工资"
    BASIC_SALARY = 2, "基础工资"
    OVERTIME_SALARY = 3, "加班工资"
    BONUS = 4, "奖金"
    HOURLY_SALARY = 5, "时薪工资"
    SALARY_DISBURSEMENT = 6, "工资发放"
    PERFORMANCE_EVALUATION = 7, "绩效"
    COMMISSION = 8, "提成"
    OTHER = 99, "其他"
    

OUT_SALSRY_ENUMS = [
    StaffSalaryTypeChoices.ADVANCE_PAYMENT,
    StaffSalaryTypeChoices.SALARY_DISBURSEMENT,
]
