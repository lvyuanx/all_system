# -*- coding:utf-8 -*-
"""
# File       : flow.py
# Description: 通用工作流模型定义
"""
from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from .enums import (
    NodeTypeChoices,
    FlowStatusChoices,
    TaskStatusChoices,
)

User = get_user_model()


class FlowDefinition(models.Model):
    """流程模板定义"""
    code = models.CharField(max_length=100, unique=True, verbose_name="流程编码")
    name = models.CharField(max_length=200, verbose_name="流程名称")
    description = models.TextField(blank=True, null=True, verbose_name="流程描述")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    version = models.CharField(max_length=50, default="v1", verbose_name="版本号")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "流程定义"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} ({self.code})"


class FlowNode(models.Model):
    """流程节点定义"""
    flow = models.ForeignKey(FlowDefinition, on_delete=models.CASCADE, related_name="nodes")
    code = models.CharField(max_length=100, verbose_name="节点编码")
    name = models.CharField(max_length=200, verbose_name="节点名称")
    node_type = models.CharField(
        max_length=20,
        choices=NodeTypeChoices.choices,
        default=NodeTypeChoices.TASK,
        verbose_name="节点类型"
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name="节点权限（可处理的系统权限）"
    )
    form_schema = models.JSONField(blank=True, null=True, verbose_name="节点表单配置")
    is_auto = models.BooleanField(default=False, verbose_name="是否自动执行")
    order = models.IntegerField(default=0, verbose_name="节点顺序")

    class Meta:
        unique_together = ("flow", "code")
        ordering = ["order"]
        verbose_name = "流程节点"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.flow.name} - {self.name}"


class FlowTransition(models.Model):
    """节点流转关系"""
    flow = models.ForeignKey(FlowDefinition, on_delete=models.CASCADE, related_name="transitions")
    source = models.ForeignKey(FlowNode, on_delete=models.CASCADE, related_name="outgoing")
    target = models.ForeignKey(FlowNode, on_delete=models.CASCADE, related_name="incoming")
    condition_expr = models.TextField(blank=True, null=True, verbose_name="条件表达式 (Python/JSON logic)")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="描述")

    class Meta:
        verbose_name = "流转条件"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.source.name} → {self.target.name}"


class FlowInstance(models.Model):
    """流程运行实例"""
    flow = models.ForeignKey(FlowDefinition, on_delete=models.CASCADE, related_name="instances")
    business_type = models.CharField(max_length=100, verbose_name="业务类型")
    business_id = models.CharField(max_length=100, verbose_name="业务ID")
    current_node = models.ForeignKey(FlowNode, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=FlowStatusChoices.choices,
        default=FlowStatusChoices.RUNNING,
        verbose_name="状态"
    )
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_flows")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    context = models.JSONField(blank=True, null=True, verbose_name="上下文变量")

    class Meta:
        unique_together = ("business_type", "business_id")
        verbose_name = "流程实例"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.flow.name} - {self.business_type}#{self.business_id}"


class FlowTask(models.Model):
    """流程任务"""
    instance = models.ForeignKey(FlowInstance, on_delete=models.CASCADE, related_name="tasks")
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=TaskStatusChoices.choices,
        default=TaskStatusChoices.PENDING,
        verbose_name="任务状态"
    )
    comment = models.TextField(blank=True, null=True, verbose_name="审批意见")
    start_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "任务记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.node.name} - {self.status}"


class FlowLog(models.Model):
    """操作日志"""
    instance = models.ForeignKey(FlowInstance, on_delete=models.CASCADE, related_name="logs")
    node = models.ForeignKey(FlowNode, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100, verbose_name="动作")
    message = models.TextField(blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-create_time"]
        verbose_name = "流程日志"
        verbose_name_plural = verbose_name


class FlowVariable(models.Model):
    """流程变量（可选）"""
    instance = models.ForeignKey(FlowInstance, on_delete=models.CASCADE, related_name="variables")
    key = models.CharField(max_length=100)
    value = models.JSONField()
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("instance", "key")
        verbose_name = "流程变量"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.key}={self.value}"
