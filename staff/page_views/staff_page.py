from django.shortcuts import render
from django.contrib.auth.models import Group

def staff_salary_cards(request):
    context = {
        "title": "工资快捷面包",
    }
    return render(request, "staff/staff_salary_cards.html", context)



def staff_salary_basic_disbursement(request):
    context = {
        "title": "基本工资发放",
    }
    return render(request, "staff/staff_salary_basic_disbursement.html", context)

