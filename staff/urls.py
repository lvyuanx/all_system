from django.urls import path
from .page_views.staff_page import staff_salary_cards, staff_salary_basic_disbursement

app_name = "staff"

urls = [
    path("staff/staffsalary/cards/", staff_salary_cards, name="staff_salary_cards"),
    path("staff/staffsalary/basic_disbursement/", staff_salary_basic_disbursement, name="staff_salary_basic_disbursement"),
]