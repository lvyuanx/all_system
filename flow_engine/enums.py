# -*- coding:utf-8 -*-
"""
# File       : menus.py
# Description: 定义所有模型共用的 choices 枚举
"""

from django.db import models


class FlowStatusChoices(models.TextChoices):
    """流程状态"""
    RUNNING = "running", "运行中"
    FINISHED = "finished", "已完成"
    CANCELED = "canceled", "已取消"


class TaskStatusChoices(models.TextChoices):
    """任务状态"""
    PENDING = "pending", "待处理"
    APPROVED = "approved", "已通过"
    REJECTED = "rejected", "已驳回"


class NodeTypeChoices(models.TextChoices):
    """节点类型"""
    START = "start", "开始节点"
    TASK = "task", "任务节点"
    CONDITION = "condition", "条件判断节点"
    END = "end", "结束节点"
