from decimal import Decimal
from staff.enums import StaffSalaryTypeChoices
from staff.models import StaffSalary


def generate_title(staff_salary: StaffSalary) -> str:
    salary_type = staff_salary.salary_type
    salary_decimal = staff_salary.salary
    salary = f"{salary_decimal:.2f}"
    create_time = staff_salary.create_time
    year = staff_salary.year
    month = staff_salary.month
    day = staff_salary.day
    basic_salary = staff_salary.basic_salary
    hourly_wage = staff_salary.hourly_wage
    work_hours = staff_salary.work_hours
    
    if salary_type == StaffSalaryTypeChoices.ADVANCE_PAYMENT:
        timestr = create_time.strftime("%Y-%m-%d %H:%M:%S")
        return f"(支出){timestr}预支工资{salary}元"
    
    assert year and isinstance(year, int), "缺少【年】参数, 或者参数格式不正确"
    assert month and isinstance(month, int), "缺少【年】参数, 或者参数格式不正确"
    
    if salary_type == StaffSalaryTypeChoices.BASIC_SALARY:
        return f"{year}年{month}月基础工资{basic_salary}元，实际工资{salary}元"

    if salary_type == StaffSalaryTypeChoices.BONUS:
        return f"{year}年{month}月奖金{salary}元"

    if salary_type == StaffSalaryTypeChoices.HOURLY_SALARY:
        assert hourly_wage and isinstance(hourly_wage, Decimal), "缺少【时薪】参数, 或者参数格式不正确"
        assert work_hours and isinstance(work_hours, int), "缺少【工时】参数, 或者参数格式不正确"
        return f"{year}年{month}月时薪工资{hourly_wage}元 * {work_hours}小时, 总计时薪工资{salary}元"
    
    if salary_type == StaffSalaryTypeChoices.SALARY_DISBURSEMENT:
        timestr = create_time.strftime("%Y-%m-%d %H:%M:%S")
        return f"(支出){timestr}发放{year}年{month}月工资{salary}元"
    
    if salary_type == StaffSalaryTypeChoices.PERFORMANCE_EVALUATION:
        return f"{year}年{month}月绩效工资{salary}元"
    
    if salary_type == StaffSalaryTypeChoices.COMMISSION:
        return f"{year}年{month}月提成工资{salary}元"
    
    if salary_type == StaffSalaryTypeChoices.OTHER:
        return f"{year}年{month}月其他工资{salary}元"
    
    assert day and isinstance(day, int), "缺少【年】参数, 或者参数格式不正确"
    
    if salary_type == StaffSalaryTypeChoices.OVERTIME_SALARY:
        return f"{year}年{month}月{day}日加班工资{salary}元"
    
    raise ValueError("无效的工资类型")

