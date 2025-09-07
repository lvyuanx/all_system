from decimal import Decimal
from pydantic import Field, BaseModel
from typing import Optional



class BasicSalaryListItemSchema(BaseModel):
    staff_code: str = Field(..., description="工号")
    full_name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    basic_salary: Decimal = Field(..., description="基础工资")
    actual_disbursement: Optional[Decimal] = Field(description="实发工资")
    memo: Optional[str] = Field(description="备注")


