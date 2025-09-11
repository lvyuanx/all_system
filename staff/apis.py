from .views.salary import staff_salary_basic_disbursement_list_view, staff_salary_basic_batch_disbursement_view

apis = {
    "salary": [
        ("A0", "basic_disbursement_list", staff_salary_basic_disbursement_list_view.View, "查询未发放工资列表"),
        ("A1", "batch_disbursement", staff_salary_basic_batch_disbursement_view.View, "工资批量发放")
    ]
}