# -*-coding:utf-8 -*-
"""
# File       : salary_machine.py
# Time       : 2025-09-02 20:10:00
# Author     : lyx
# version    : python 3.11
# Description: 工资状态机（整数枚举 + State + 自动日志）
"""

from transitions import Machine, State
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from staff.models import StaffSalary
from .enums import StaffSalaryStatusChoices


class StaffSalaryStateMachine:
    """
    使用示例：
    s = StaffSalary.objects.create(staff_name="小王", salary=8000)
    sm = StaffSalaryStateMachine(s, audit_user=request.user)
    sm.audit_pass()
    sm.save_state()
    """

    # 定义状态，Machine 内部用字符串
    states = [
        State(name=str(StaffSalaryStatusChoices.UNAUDIT)),
        State(name=str(StaffSalaryStatusChoices.PENDING_CORRECTION)),
        State(name=str(StaffSalaryStatusChoices.CORRECTIONED)),
        State(name=str(StaffSalaryStatusChoices.AUDIT_PASS)),
        State(name=str(StaffSalaryStatusChoices.AUDIT_REJECT)),
        State(name=str(StaffSalaryStatusChoices.CANCEL)),
    ]

    # 定义状态流转
    transitions = [
        {
            "trigger": "audit_pass",
            "source": [
                str(StaffSalaryStatusChoices.UNAUDIT),
                str(StaffSalaryStatusChoices.CORRECTIONED),
            ],
            "dest": str(StaffSalaryStatusChoices.AUDIT_PASS),
        },
        {
            "trigger": "audit_correction",
            "source": [
                str(StaffSalaryStatusChoices.UNAUDIT),
                str(StaffSalaryStatusChoices.CORRECTIONED),
            ],
            "dest": str(StaffSalaryStatusChoices.PENDING_CORRECTION),
        },
        {
            "trigger": "audit_reject",
            "source": [
                str(StaffSalaryStatusChoices.UNAUDIT),
                str(StaffSalaryStatusChoices.CORRECTIONED),
            ],
            "dest": str(StaffSalaryStatusChoices.AUDIT_REJECT),
        },
        {
            "trigger": "correction",
            "source": str(StaffSalaryStatusChoices.PENDING_CORRECTION),
            "dest": str(StaffSalaryStatusChoices.CORRECTIONED),
        },
        {
            "trigger": "cancel",
            "source": [
                str(StaffSalaryStatusChoices.UNAUDIT),
                str(StaffSalaryStatusChoices.PENDING_CORRECTION),
                str(StaffSalaryStatusChoices.CORRECTIONED),
            ],
            "dest": str(StaffSalaryStatusChoices.CANCEL),
        },
    ]

    def __init__(self, salary_obj: StaffSalary, audit_user: AbstractUser = None, audit_memo: str =None):
        self.salary = salary_obj
        self.audit_user = audit_user
        self.audit_memo = audit_memo
        # 将整数初始状态转换成字符串 State
        initial_state = str(salary_obj.status)

        self.machine = Machine(
            model=self,
            states=StaffSalaryStateMachine.states,
            transitions=StaffSalaryStateMachine.transitions,
            initial=initial_state,
            auto_transitions=False,  # 严格控制状态流转
            after_state_change="log_transition",
        )

    def save_state(self):
        """
        保存状态到工资单
        """
        self.salary.status = int(self.state)  # 转回整数枚举
        if self.audit_memo:
            self.salary.audit_memo = self.audit_memo
        self.salary.save()

    def log_transition(self):
        """
        状态变更后写 StaffSalaryCa 日志
        """
        from .models import StaffSalaryCa  # 避免循环导入

        StaffSalaryCa.objects.create(
            staff_salary=self.salary,
            salary_serial_number=self.salary.salary_serial_number,
            pre_status=int(self.salary.status),  # 切换前状态
            cur_status=int(self.state),          # 切换后状态
            audit_user=self.audit_user,
            audit_full_name=getattr(self.audit_user, "full_name", None),
            audit_user_phone=getattr(self.audit_user, "phone", None),
            audit_time=timezone.now(),
            audit_memo=self.audit_memo,
        )
