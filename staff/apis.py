from .views.salary import staff_salary_basic_disbursement_view

apis = {
    "salary": [
        ("A0", "padding_salary", staff_salary_basic_disbursement_view.View, "查询未发放工资列表")
    ]
}