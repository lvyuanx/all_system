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
    REJECTED = "rejected", "已驳回"


class TaskStatusChoices(models.TextChoices):
    """任务状态"""
    PENDING = "pending", "待处理"
    APPROVED = "approved", "已通过"
    REJECTED = "rejected", "已驳回"
    CANCELED = "canceled", "已取消"
    DONE = "done", "已完成"


class NodeTypeChoices(models.TextChoices):
    """节点类型"""
    START = "start", "开始节点"
    TASK = "task", "任务节点"
    CONDITION = "condition", "条件判断节点"
    END = "end", "结束节点"


class ApprovalModeChoices(models.TextChoices):
    """节点审批模式"""
    ANY = "any", "任意满足"
    ALL = "all", "全部满足"


class RuleTypeChoices(models.TextChoices):
    """节点授权规则类型"""
    PERM_PACK = "perm_pack", "权限包"
    USER = "user", "指定人"


class FlowVersionStatusChoices(models.TextChoices):
    """流程版本状态"""
    DRAFT = "draft", "草稿"
    PUBLISHED = "published", "已发布"
    RETIRED = "retired", "已停用"


class FlowMigrationStatusChoices(models.TextChoices):
    """迁移任务状态"""
    PENDING = "pending", "待执行"
    RUNNING = "running", "执行中"
    SUCCESS = "success", "成功"
    FAILED = "failed", "失败"
