from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.models import Group

from core.utils import time_util
from staff.models import StaffSalary, StaffSalaryCa
from staff.enums import StaffSalaryStatusChoices

def staff_salary_cards(request):
    context = {
        "title": "工资快捷面板",
    }
    return render(request, "staff/staff_salary_cards.html", context)



def staff_salary_basic_disbursement(request):
    context = {
        "title": "基本工资发放",
    }
    return render(request, "staff/staff_salary_basic_disbursement.html", context)


audit_title_dict = {
    StaffSalaryStatusChoices.AUDIT_PASS: "审核已通过，申请已被批准",
    StaffSalaryStatusChoices.PENDING_CORRECTION: "申请需修正，等待修正后重新提交",
    StaffSalaryStatusChoices.CORRECTIONED: "修正申请已提交，待审核",
    StaffSalaryStatusChoices.AUDIT_REJECT: "审核未通过，申请被拒绝",
    StaffSalaryStatusChoices.CANCEL: "申请已取消，流程终止",
}


def staff_salary_autit_timeline(request, ssid: int):
    
    ss_manager = StaffSalary.objects.filter(pk=ssid)
    if not ss_manager.exists():
        raise Http404()
    
    ss_obj = ss_manager.values("create_user__full_name", "create_user__phone", "create_time").first()
    audit_lst = [{
        "audit_title": "创建了一条申请",
        "audit_user": ss_obj["create_user__full_name"],
        "audit_user_phone": ss_obj["create_user__phone"],
        "audit_time": time_util.datetime_to_str(ss_obj["create_time"]),
        "audit_memo": ""
    }]
    
    # 获取CA记录
    ss_ca_manager = StaffSalaryCa.objects.filter(staff_salary_id=ssid).order_by("id").values(
        "audit_full_name",
        "audit_user_phone",
        "audit_time",
        "audit_memo",
        "cur_status",
    )
    for ss_ca_obj in ss_ca_manager:
        ss_ca_obj = {
            "audit_user": ss_ca_obj["audit_full_name"],
            "audit_user_phone": ss_ca_obj["audit_user_phone"],
            "audit_time": time_util.datetime_to_str(ss_ca_obj["audit_time"]),
            "audit_memo": ss_ca_obj["audit_memo"],
            "audit_title": audit_title_dict.get(StaffSalaryStatusChoices(ss_ca_obj["cur_status"])),
        }
        audit_lst.append(ss_ca_obj)
    
    context = {
        "title": "工资审核时间线",
        "audit_lst": audit_lst,
    }
    return render(request, "staff/staff_salary_autit_timeline.html", context)



def staff_salary_hourly_disbursement(request):
    context = {
        "title": "时薪工资发放",
    }
    return render(request, "staff/staff_salary_hourly_disbursement.html", context)

