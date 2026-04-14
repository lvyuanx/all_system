# -*- coding:utf-8 -*-
"""
# File       : flow.py
# Description: 通用工作流模型定义
"""
from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from core.auth.models import PermissionPack
from .enums import (
    NodeTypeChoices,
    FlowStatusChoices,
    TaskStatusChoices,
    ApprovalModeChoices,
    RuleTypeChoices,
    FlowVersionStatusChoices,
    FlowMigrationStatusChoices,
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


class FlowForm(models.Model):
    """独立表单定义，可被任意流程节点引用"""
    code = models.CharField(max_length=100, unique=True, verbose_name="表单编码")
    name = models.CharField(max_length=200, verbose_name="表单名称")
    group_name = models.CharField(max_length=100, blank=True, default="", verbose_name="表单分组")
    description = models.TextField(blank=True, null=True, verbose_name="表单描述")
    form_schema = models.JSONField(blank=True, null=True, verbose_name="表单配置")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["group_name", "code"]
        verbose_name = "表单定义"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} ({self.code})"


class FlowVersion(models.Model):
    """Flow definition snapshot version"""
    definition = models.ForeignKey(
        FlowDefinition, on_delete=models.CASCADE, related_name="versions"
    )
    version_no = models.IntegerField(default=1, verbose_name="Version No")
    status = models.CharField(
        max_length=20,
        choices=FlowVersionStatusChoices.choices,
        default=FlowVersionStatusChoices.DRAFT,
    )
    snapshot_json = models.JSONField(blank=True, null=True)
    snapshot_hash = models.CharField(max_length=128, blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    retired_at = models.DateTimeField(blank=True, null=True)
    published_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="published_flow_versions"
    )
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("definition", "version_no")
        ordering = ["-version_no"]
        verbose_name = "Flow Version"
        verbose_name_plural = verbose_name

    @property
    def version_label(self):
        return f"v{self.version_no}"

    def __str__(self):
        return f"{self.definition.name} ({self.version_label})"


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
    approval_mode = models.CharField(
        max_length=10,
        choices=ApprovalModeChoices.choices,
        default=ApprovalModeChoices.ANY,
        verbose_name="approval_mode",
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


class FlowNodeVersion(models.Model):
    """Flow node snapshot"""
    flow_version = models.ForeignKey(
        FlowVersion, on_delete=models.CASCADE, related_name="nodes"
    )
    code = models.CharField(max_length=100, verbose_name="Node Code")
    name = models.CharField(max_length=200, verbose_name="Node Name")
    node_type = models.CharField(
        max_length=20,
        choices=NodeTypeChoices.choices,
        default=NodeTypeChoices.TASK,
    )
    approval_mode = models.CharField(
        max_length=10,
        choices=ApprovalModeChoices.choices,
        default=ApprovalModeChoices.ANY,
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name="Node Permissions",
    )
    form_schema = models.JSONField(blank=True, null=True)
    is_auto = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ("flow_version", "code")
        ordering = ["order"]
        verbose_name = "Flow Node Version"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.flow_version.definition.name} - {self.name} ({self.flow_version.version_label})"


class FlowTransitionVersion(models.Model):
    """Flow transition snapshot"""
    flow_version = models.ForeignKey(
        FlowVersion, on_delete=models.CASCADE, related_name="transitions"
    )
    source = models.ForeignKey(
        FlowNodeVersion, on_delete=models.CASCADE, related_name="outgoing_transitions"
    )
    target = models.ForeignKey(
        FlowNodeVersion, on_delete=models.CASCADE, related_name="incoming_transitions"
    )
    condition_expr = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Flow Transition Version"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.source.name} -> {self.target.name}"


class FlowNodeGroup(models.Model):
    """Node approval group (definition or version)"""
    node = models.ForeignKey(
        FlowNode,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="groups",
    )
    node_version = models.ForeignKey(
        FlowNodeVersion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="groups",
    )
    key = models.CharField(max_length=50, verbose_name="Group Key")
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Group Name")
    min_approve_count = models.IntegerField(default=1, verbose_name="Min Approvals")
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Flow Node Group"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.key} ({self.min_approve_count})"


class FlowNodeGroupRule(models.Model):
    """Group rule mapping to permission packs or users"""
    group = models.ForeignKey(
        FlowNodeGroup, on_delete=models.CASCADE, related_name="rules"
    )
    rule_type = models.CharField(
        max_length=20,
        choices=RuleTypeChoices.choices,
        default=RuleTypeChoices.PERM_PACK,
    )
    perm_pack = models.ForeignKey(
        PermissionPack,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flow_node_rules",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flow_node_rules",
    )

    class Meta:
        verbose_name = "Flow Node Group Rule"
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.rule_type == RuleTypeChoices.USER and self.user:
            return f"user:{self.user}"
        if self.rule_type == RuleTypeChoices.PERM_PACK and self.perm_pack:
            return f"pack:{self.perm_pack.pack_code}"
        return self.rule_type


class FlowInstance(models.Model):
    """流程运行实例"""
    flow = models.ForeignKey(FlowDefinition, on_delete=models.CASCADE, related_name="instances")
    flow_version = models.ForeignKey(
        FlowVersion,
        on_delete=models.PROTECT,
        related_name="instances",
        null=True,
        blank=True,
    )
    business_type = models.CharField(max_length=100, verbose_name="业务类型")
    business_id = models.CharField(max_length=100, verbose_name="业务ID")
    current_node = models.ForeignKey(
        FlowNodeVersion, on_delete=models.SET_NULL, null=True, blank=True
    )
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
    node = models.ForeignKey(FlowNodeVersion, on_delete=models.CASCADE)
    group_key = models.CharField(max_length=50, null=True, blank=True)
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
    node = models.ForeignKey(FlowNodeVersion, on_delete=models.SET_NULL, null=True, blank=True)
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


class FlowMigrationPlan(models.Model):
    """Flow version migration plan"""
    definition = models.ForeignKey(
        FlowDefinition, on_delete=models.CASCADE, related_name="migration_plans"
    )
    from_version = models.ForeignKey(
        FlowVersion,
        on_delete=models.CASCADE,
        related_name="migration_from_plans",
    )
    to_version = models.ForeignKey(
        FlowVersion,
        on_delete=models.CASCADE,
        related_name="migration_to_plans",
    )
    status = models.CharField(
        max_length=20,
        choices=FlowVersionStatusChoices.choices,
        default=FlowVersionStatusChoices.DRAFT,
    )
    rule_json = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_migration_plans"
    )
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Flow Migration Plan"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.definition.name}: {self.from_version.version_label} -> {self.to_version.version_label}"


class FlowMigrationJob(models.Model):
    """Flow instance migration job"""
    plan = models.ForeignKey(
        FlowMigrationPlan, on_delete=models.CASCADE, related_name="jobs"
    )
    instance = models.ForeignKey(
        FlowInstance, on_delete=models.CASCADE, related_name="migration_jobs"
    )
    status = models.CharField(
        max_length=20,
        choices=FlowMigrationStatusChoices.choices,
        default=FlowMigrationStatusChoices.PENDING,
    )
    result_json = models.JSONField(blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Flow Migration Job"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.plan_id} - {self.instance_id} ({self.status})"
