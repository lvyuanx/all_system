#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@File    : machine.py
@Author  : lvyuanxiang
@Time    : 2026-02-05
@Desc    :
    工资状态机
"""


from transitions import Machine, State
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from  order.models import Order, OrderCa
from .enums import OrderStatusChoices
from core.utils import time_util


class OrderStateMachine:

    # 定义状态，Machine 内部用字符串
    states = [
        State(name=str(OrderStatusChoices.CANCELED)),
        State(name=str(OrderStatusChoices.CREATED)),
        State(name=str(OrderStatusChoices.CONFIRMED)),
        State(name=str(OrderStatusChoices.SCHEDULED)),
        State(name=str(OrderStatusChoices.PRODUCING)),
        State(name=str(OrderStatusChoices.FINISHED)),
        State(name=str(OrderStatusChoices.SHIPPED)),
        State(name=str(OrderStatusChoices.COMPLETED)),
    ]

    # 定义状态流转
    transitions = [
        # 创建 -> 确认
        {
            "trigger": "confirm",
            "source": str(OrderStatusChoices.CREATED),
            "dest": str(OrderStatusChoices.CONFIRMED),
        },
        # 确认 -> 排产
        {
            "trigger": "schedule",
            "source": str(OrderStatusChoices.CONFIRMED),
            "dest": str(OrderStatusChoices.SCHEDULED),
        },
        # 排产 -> 生产中
        {
            "trigger": "start_production",
            "source": str(OrderStatusChoices.SCHEDULED),
            "dest": str(OrderStatusChoices.PRODUCING),
        },
        # 生产中 -> 完工
        {
            "trigger": "finish_production",
            "source": str(OrderStatusChoices.PRODUCING),
            "dest": str(OrderStatusChoices.FINISHED),
        },
        # 完工 -> 发货
        {
            "trigger": "ship",
            "source": str(OrderStatusChoices.FINISHED),
            "dest": str(OrderStatusChoices.SHIPPED),
        },
        # 发货 -> 完成
        {
            "trigger": "complete",
            "source": str(OrderStatusChoices.SHIPPED),
            "dest": str(OrderStatusChoices.COMPLETED),
        },
        # 取消（只允许在排产前取消）
        {
            "trigger": "cancel",
            "source": [
                str(OrderStatusChoices.CREATED),
                str(OrderStatusChoices.CONFIRMED),
            ],
            "dest": str(OrderStatusChoices.CANCELED),
        },
    ]

    def __init__(
        self,
        model_obj: Order,
        operator_user: AbstractUser = None, 
        operator_memo: str =None
    ):
        self.model_obj: Order = model_obj
        self.operator_user = operator_user
        self.operator_memo = operator_memo
        # 将整数初始状态转换成字符串 State
        initial_state = str(model_obj.order_status)

        self.machine = Machine(
            model=self,
            states=self.states,
            transitions=self.transitions,
            initial=initial_state,
            auto_transitions=False,  # 严格控制状态流转
            after_state_change="log_transition",
        )

    def save_state(self):
        """
        保存状态到工资单
        """
        self.model_obj.order_status = int(self.state)  # 转回整数枚举
        self.model_obj.save()

    def log_transition(self):
        """
        状态变更后写 StaffSalaryCa 日志
        """

        OrderCa.objects.create(
            order_no=self.model_obj.order_no,
            order=self.model_obj,
            operator=self.operator_user,
            operator_memo=self.operator_memo,
            operator_name=getattr(self.operator_user, "full_name", None),
            operator_phone=getattr(self.operator_user, "phone", None),
            operator_time=time_util.now(),
            cur_status=int(self.state),
            pre_status=int(self.model_obj.order_status),
        )
