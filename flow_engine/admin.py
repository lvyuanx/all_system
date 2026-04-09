from django.contrib import admin

from flow_engine.models import (
    FlowDefinition,
    FlowVersion,
    FlowNode,
    FlowTransition,
    FlowNodeVersion,
    FlowTransitionVersion,
    FlowNodeGroup,
    FlowNodeGroupRule,
    FlowInstance,
    FlowTask,
    FlowLog,
    FlowMigrationPlan,
    FlowMigrationJob,
)
from flow_engine.flow_engine import FlowEngine
from django.utils.html import format_html
from django.urls import reverse


@admin.register(FlowDefinition)
class FlowDefinitionAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "version", "is_active", "designer_link", "create_time", "update_time")
    search_fields = ("code", "name")
    actions = ["publish_versions"]

    def designer_link(self, obj):
        url = reverse("flow_definition_change", kwargs={"fid": obj.pk})
        return format_html('<a href="{}">设计器</a>', url)

    designer_link.short_description = "设计器"

    def publish_versions(self, request, queryset):
        count = 0
        for flow_def in queryset:
            FlowEngine.publish_definition(flow_def, published_by=request.user)
            count += 1
        self.message_user(request, f"Published {count} flow version(s).")


@admin.register(FlowVersion)
class FlowVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "definition", "version_no", "status", "published_at")
    list_filter = ("status",)
    search_fields = ("definition__code", "definition__name")


@admin.register(FlowNode)
class FlowNodeAdmin(admin.ModelAdmin):
    list_display = ("id", "flow", "code", "name", "node_type", "approval_mode", "order")
    list_filter = ("flow", "node_type")
    search_fields = ("code", "name")


@admin.register(FlowTransition)
class FlowTransitionAdmin(admin.ModelAdmin):
    list_display = ("id", "flow", "source", "target")
    list_filter = ("flow",)


@admin.register(FlowNodeVersion)
class FlowNodeVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "flow_version", "code", "name", "node_type", "approval_mode", "order")
    list_filter = ("flow_version", "node_type")
    search_fields = ("code", "name")


@admin.register(FlowTransitionVersion)
class FlowTransitionVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "flow_version", "source", "target")
    list_filter = ("flow_version",)


@admin.register(FlowNodeGroup)
class FlowNodeGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "name", "min_approve_count", "order")
    list_filter = ("node", "node_version")


@admin.register(FlowNodeGroupRule)
class FlowNodeGroupRuleAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "rule_type", "perm_pack", "user")
    list_filter = ("rule_type",)


@admin.register(FlowInstance)
class FlowInstanceAdmin(admin.ModelAdmin):
    list_display = ("id", "flow", "flow_version", "business_type", "business_id", "status", "create_time")
    list_filter = ("status", "flow")
    search_fields = ("business_type", "business_id")


@admin.register(FlowTask)
class FlowTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "instance", "node", "assignee", "group_key", "status", "start_time", "finish_time")
    list_filter = ("status", "node")
    search_fields = ("instance__business_id",)


@admin.register(FlowLog)
class FlowLogAdmin(admin.ModelAdmin):
    list_display = ("id", "instance", "node", "user", "action", "create_time")
    list_filter = ("action",)


@admin.register(FlowMigrationPlan)
class FlowMigrationPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "definition", "from_version", "to_version", "status", "create_time")
    list_filter = ("status", "definition")


@admin.register(FlowMigrationJob)
class FlowMigrationJobAdmin(admin.ModelAdmin):
    list_display = ("id", "plan", "instance", "status", "create_time", "finish_time")
    list_filter = ("status",)
