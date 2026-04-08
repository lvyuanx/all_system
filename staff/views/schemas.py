from decimal import Decimal
from pydantic import Field, BaseModel
from typing import Optional
from ..enums import StaffSalaryTypeChoices
from datetime import datetime



class BasicSalaryListItemSchema(BaseModel):
    sid: int = Field(..., description="员工id")
    staff_code: str = Field(..., description="工号")
    full_name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    basic_salary: Decimal = Field(..., description="基础工资")
    actual_disbursement: Decimal = Field(..., description="实发工资")
    memo: Optional[str] = Field(None, description="备注")
    

class BasicSalaryBatchDisbursementSchema(BaseModel):
    data: list[BasicSalaryListItemSchema] = Field(..., description="发放基础工资列表")
    year: int = Field(..., ge=2000, description="发放年份")
    month: int = Field(..., ge=1, le=12, description="发放月份")


class HourlyStaffSalaryListItemSchema(BaseModel):
    sid: int = Field(..., description="员工id")
    staff_code: str = Field(..., description="工号")
    full_name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    staff_hourly_wage: Decimal = Field(..., description="员工时薪（元）")
    hourly_wage: Decimal = Field(..., description="实发时薪（元）")
    work_hours: Decimal = Field(..., description="总工时")
    actual_disbursement: Decimal = Field(..., description="实发工资（元）")
    memo: Optional[str] = Field(None, description="备注")


class BasicHourlyBatchDisbursementSchema(BaseModel):
    data: list[HourlyStaffSalaryListItemSchema] = Field(..., description="发放基础工资列表")
    year: int = Field(..., ge=2000, description="发放年份")
    month: int = Field(..., ge=1, le=12, description="发放月份")
    
    
class SalaryListItemSchema(BaseModel):
    sid: int = Field(..., description="员工id")
    staff_code: str = Field(..., description="工号")
    full_name: str = Field(..., description="姓名")
    phone: str = Field(..., description="手机号")
    actual_disbursement: Decimal = Field(..., description="实发工资")
    disbursement_time: datetime = Field(..., description="发放时间")
    memo: Optional[str] = Field(None, description="备注")
    

class SalaryBatchDisbursementSchema(BaseModel):
    data: list[SalaryListItemSchema] = Field(..., description="发放工资列表")
    salary_type: StaffSalaryTypeChoices = Field(..., description="发放工资类型")




class SalaryQuickDataReqSchema(BaseModel):
    start: datetime | None = Field(default=None, description="开始时间")
    end: datetime | None = Field(default=None, description="结束时间")

class SalaryQuickDataSchema(BaseModel):
    wait_distribution_basic_count: int = Field(..., description="本月基础工资待发放")
    wait_audit_count: int = Field(..., description="待审批数量")
    wait_release_count: int = Field(..., description="待发放数量")
    wait_correction_count: int = Field(..., description="待修正数量")
    basic_salary: Decimal = Field(..., description="基础工资")
    overtime_salary: Decimal = Field(..., description="加班工资")
    bonus_salary: Decimal = Field(..., description="奖金")
    hourly_salary: Decimal = Field(..., description="时薪工资")
    performance_evaluation_salary: Decimal = Field(..., description="绩效")
    commission_salary: Decimal = Field(..., description="提成")
    other_salary: Decimal = Field(..., description="其他")

class MobileStaffInfoSchema(BaseModel):
    staff_code: str | None = Field(default=None, description="??")
    site_name: str | None = Field(default=None, description="??????")


class MobileStaffListItemSchema(BaseModel):
    staff_id: int = Field(..., description="员工ID")
    user_id: int = Field(..., description="用户ID")
    staff_code: str = Field(..., description="工号")
    full_name: str | None = Field(default=None, description="姓名")
    username: str = Field(..., description="用户名")
    phone: str | None = Field(default=None, description="手机号")
    avatar: str | None = Field(default=None, description="头像")
    is_active: bool = Field(..., description="账号是否启用")
    site_name: str | None = Field(default=None, description="所属站点")
    group_names: list[str] = Field(default_factory=list, description="权限组名称列表")


class MobileStaffDetailSchema(BaseModel):
    staff_id: int = Field(..., description="员工ID")
    user_id: int = Field(..., description="用户ID")
    staff_code: str = Field(..., description="工号")
    full_name: str | None = Field(default=None, description="姓名")
    username: str = Field(..., description="用户名")
    first_name: str | None = Field(default=None, description="名")
    last_name: str | None = Field(default=None, description="姓")
    email: str | None = Field(default=None, description="邮箱")
    phone: str | None = Field(default=None, description="手机号")
    sex: str | None = Field(default=None, description="性别")
    age: int | None = Field(default=None, description="年龄")
    avatar: str | None = Field(default=None, description="头像")
    is_active: bool = Field(..., description="账号是否启用")
    site_id: int | None = Field(default=None, description="所属站点ID")
    site_name: str | None = Field(default=None, description="所属站点")
    group_ids: list[int] = Field(default_factory=list, description="权限组ID列表")
    group_names: list[str] = Field(default_factory=list, description="权限组名称列表")


class MobileStaffStatusChangeSchema(BaseModel):
    user_id: int = Field(..., description="用户ID")


class MobileStaffUpdateGroupsSchema(BaseModel):
    user_id: int = Field(..., description="用户ID")
    group_ids: list[int] = Field(default_factory=list, description="权限组ID列表")


class MobileGroupOptionSchema(BaseModel):
    group_id: int = Field(..., description="权限组ID")
    group_name: str = Field(..., description="权限组名称")
