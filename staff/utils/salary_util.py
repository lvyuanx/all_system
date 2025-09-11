from decimal import Decimal
from staff.enums import StaffSalaryTypeChoices
from staff.models import StaffSalary


from decimal import Decimal
from typing import Union
from datetime import datetime

def generate_title(staff_salary: Union[dict, "StaffSalary"]) -> str:
    # 如果传入的是 model 对象，先转成 dict
    if not isinstance(staff_salary, dict):
        # 假设你的 model 有一个 to_dict 方法
        if hasattr(staff_salary, "to_dict"):
            staff_salary = staff_salary.to_dict()
        else:
            # 用 __dict__ 简单转（Django 模型用 model_to_dict 更合适）
            from django.forms.models import model_to_dict
            staff_salary = model_to_dict(staff_salary)
    
    # 取值
    salary_type = staff_salary.get("salary_type")
    salary_decimal = staff_salary.get("salary")
    salary = f"{salary_decimal:.2f}" if salary_decimal is not None else "0.00"
    create_time = staff_salary.get("create_time")
    year = staff_salary.get("year")
    month = staff_salary.get("month")
    day = staff_salary.get("day")
    basic_salary = staff_salary.get("basic_salary")
    hourly_wage = staff_salary.get("hourly_wage")
    work_hours = staff_salary.get("work_hours")

    if salary_type == StaffSalaryTypeChoices.ADVANCE_PAYMENT:
        timestr = create_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(create_time, datetime) else str(create_time)
        return f"(支出){timestr}预支工资{salary}元"

    assert year and isinstance(year, int), "缺少【年】参数, 或者参数格式不正确"
    assert month and isinstance(month, int), "缺少【月】参数, 或者参数格式不正确"

    if salary_type == StaffSalaryTypeChoices.BASIC_SALARY:
        return f"{year}年{month}月基础工资{basic_salary}元，实际工资{salary}元"

    if salary_type == StaffSalaryTypeChoices.BONUS:
        return f"{year}年{month}月奖金{salary}元"

    if salary_type == StaffSalaryTypeChoices.HOURLY_SALARY:
        assert hourly_wage and isinstance(hourly_wage, Decimal), "缺少【时薪】参数, 或者参数格式不正确"
        assert work_hours and isinstance(work_hours, int), "缺少【工时】参数, 或者参数格式不正确"
        return f"{year}年{month}月时薪工资{hourly_wage}元 * {work_hours}小时, 总计时薪工资{salary}元"

    if salary_type == StaffSalaryTypeChoices.SALARY_DISBURSEMENT:
        timestr = create_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(create_time, datetime) else str(create_time)
        return f"(支出){timestr}发放{year}年{month}月工资{salary}元"

    if salary_type == StaffSalaryTypeChoices.PERFORMANCE_EVALUATION:
        return f"{year}年{month}月绩效工资{salary}元"

    if salary_type == StaffSalaryTypeChoices.COMMISSION:
        return f"{year}年{month}月提成工资{salary}元"

    if salary_type == StaffSalaryTypeChoices.OTHER:
        return f"{year}年{month}月其他工资{salary}元"

    assert day and isinstance(day, int), "缺少【日】参数, 或者参数格式不正确"

    if salary_type == StaffSalaryTypeChoices.OVERTIME_SALARY:
        return f"{year}年{month}月{day}日加班工资{salary}元"

    raise ValueError("无效的工资类型")

