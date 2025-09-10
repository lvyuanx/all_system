from decimal import Decimal
from pydantic import Field, BaseModel
from typing import Optional



class BasicSalaryListItemSchema(BaseModel):
    sid: int = Field(..., description="员工id")
    staff_code: str = Field(..., description="工号")
    full_name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    basic_salary: Decimal = Field(..., description="基础工资")
    max_salary: Decimal = Field(..., description="最大可发工资")
    actual_disbursement: Decimal = Field(..., description="实发工资")
    overspend: Optional[Decimal] = Field(None, description="超支工资")
    memo: Optional[str] = Field(None, description="备注")


