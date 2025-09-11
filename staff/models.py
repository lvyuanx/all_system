from asgiref.sync import sync_to_async
from datetime import date
from decimal import Decimal
from functools import partial
from django.conf import settings
from django.db import models
from core.utils import model_util
from staff.enums import (
    StaffIncomeExpenseChoices,
    StaffSalaryStatusChoices,
    StaffSalaryTypeChoices,
)
from core.common.generator import sn_generator


class Staff(model_util.PermissionHelperMixin, models.Model):

    user = models.OneToOneField(
        "core_auth.User",
        on_delete=models.CASCADE,
        related_name="staff",
        verbose_name="用户",
    )
    staff_code = models.CharField(max_length=50, verbose_name="员工编号")
    basic_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="月基础工资",
    )
    hourly_wage = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="时薪"
    )
    account_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="账户余额"
    )
    account_total_expenditure= models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="账户总支出",
    )


    class Meta:
        verbose_name = "员工列表"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"{self.staff_code}:{self.user.full_name}"


class StaffSalary(
    model_util.PermissionHelperMixin, model_util.StructureMoelMixin, models.Model
):

    staff = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        related_name="salaries",
        verbose_name="员工",
    )
    staff_code = models.CharField(max_length=50, verbose_name="工号")
    full_name = models.CharField(max_length=50, verbose_name="姓名")
    phone = models.CharField(max_length=50, verbose_name="手机号码")
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, verbose_name="金额")
    income_expense = models.IntegerField(
        choices=StaffIncomeExpenseChoices.choices,
        default=StaffIncomeExpenseChoices.INCOME,
        verbose_name="收入支出",
    )
    memo = models.CharField(max_length=255, null=True, blank=True, verbose_name="备注")
    status = models.IntegerField(
        choices=StaffSalaryStatusChoices.choices,
        default=StaffSalaryStatusChoices.UNAUDIT,
        verbose_name="收支状态",
    )
    salary_type = models.IntegerField(
        choices=StaffSalaryTypeChoices.choices, verbose_name="工资类型"
    )
    audit_memo = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="审核备注"
    )
    year = models.IntegerField(
        verbose_name="年", default=date.today().year, null=True, blank=True
    )
    month = models.IntegerField(
        verbose_name="月", default=date.today().month, null=True, blank=True
    )
    day = models.IntegerField(
        verbose_name="日", default=date.today().day, null=True, blank=True
    )
    title = models.CharField(
        max_length=255, null=True, blank=True, default=None, verbose_name="标题"
    )

    # 基本工资使用字段
    basic_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
        verbose_name="基础工资",
    )

    # 时薪工资使用字段
    staff_hourly_wage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
        verbose_name="员工时薪",
    )
    hourly_wage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
        verbose_name="实际时薪",
    )
    work_hours = models.IntegerField(
        null=True, blank=True, default=None, verbose_name="工时"
    )

    # 支出类使用字段
    is_release = models.BooleanField(
        default=None, null=True, blank=True, verbose_name="是否发放"
    )
    release_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
        verbose_name="发放人",
        related_name="release_user"
    )

    salary_serial_number = models.CharField(
        max_length=50, verbose_name="工资流水号", unique=True
    )
    
    
    @staticmethod
    def get_sn(count=1):
        return sn_generator.next_ids(count, prefix="GZ", used_for="staff.StaffSalary", letter_length=0)
    
    @staticmethod
    async def aget_sn(count=1):
        return sync_to_async(StaffSalary.get_sn)(count)
    
    def save(self, *args, **kwargs):
        if not self.salary_serial_number:  # 只有保存时才生成
            self.salary_serial_number = self.get_sn()
        if not self.salary:
            self.salary = Decimal("0.00")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "工资收入支出情况"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"[{self.staff}]:({StaffIncomeExpenseChoices(self.income_expense).label}){StaffSalaryTypeChoices(self.salary_type).label}:{self.salary}"


class StaffSalaryCa(model_util.PermissionHelperMixin, models.Model):
    """员工工资审核表"""

    staff_salary = models.ForeignKey(
        StaffSalary,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="salary_ca",
        verbose_name="员工工资",
    )
    salary_serial_number = models.CharField(
        max_length=64, null=True, verbose_name="流水号"
    )
    pre_status = models.IntegerField(
        choices=StaffSalaryStatusChoices.choices, verbose_name="原始状态"
    )
    cur_status = models.IntegerField(
        choices=StaffSalaryStatusChoices.choices, verbose_name="当前状态"
    )
    audit_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="salary_audit_user",
        db_constraint=False,
        verbose_name="审核人",
    )
    audit_full_name = models.CharField(max_length=50, verbose_name="审核人姓名")
    audit_user_phone = models.CharField(max_length=50, verbose_name="审核人手机号码")
    audit_time = models.DateTimeField(verbose_name="审核时间", null=True)
    audit_memo = models.TextField(verbose_name="审核备注", null=True)

    class Meta:
        verbose_name = "工资收支情况审核"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.salary_serial_number}:{StaffSalaryStatusChoices(self.cur_status).label}"
