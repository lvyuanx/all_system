from decimal import Decimal
from pydantic import Field, BaseModel
from typing import Optional



class BasicSalaryListItemSchema(BaseModel):
    sid: int = Field(..., description="员工id")
    staff_code: str = Field(..., description="工号")
    full_name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    basic_salary: Decimal = Field(..., description="基础工资")
    account_balance: Decimal = Field(None, description="账户余额")
    max_salary: Decimal = Field(..., description="最大可发工资")
    actual_disbursement: Decimal = Field(..., description="实发工资")
    memo: Optional[str] = Field(None, description="备注")


class HourlyStaffSalaryListItemSchema(BaseModel):
    staff_code: str = Field(..., description="工号")
    full_name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    account_balance: Decimal = Field(..., description="账户余额（元）")
    staff_hourly_wage: Decimal = Field(..., description="员工时薪（元）")
    hourly_wage: Decimal = Field(..., description="实发时薪（元）")
    work_hours: Decimal = Field(..., description="总工时（天）")
    actual_disbursement: Decimal = Field(..., description="实发工资（元）")
    memo: Optional[str] = Field(None, description="备注")

