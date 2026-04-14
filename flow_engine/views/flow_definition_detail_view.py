# -*-coding:utf-8 -*-

"""
# Description: flow definition detail for designer
"""

from asgiref.sync import sync_to_async
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import FlowDefinition, FlowNode, FlowTransition
from flow_engine.utils.form_library_util import strip_form_library
from . import schemas


def build_flow_definition_detail(flow_def: FlowDefinition) -> schemas.FlowDefinitionDetailSchema:
    node_rows = list(FlowNode.objects.filter(flow=flow_def).order_by("order", "id"))
    nodes = []
    for node in node_rows:
        groups = []
        for group in node.groups.all().order_by("order", "id"):
            rules = [
                schemas.FlowNodeRuleSchema(
                    rule_type=rule.rule_type,
                    perm_pack_id=rule.perm_pack_id,
                    user_id=rule.user_id,
                )
                for rule in group.rules.all()
            ]
            groups.append(
                schemas.FlowNodeGroupSchema(
                    key=group.key,
                    name=group.name,
                    min_approve_count=group.min_approve_count,
                    order=group.order,
                    rules=rules,
                )
            )
        nodes.append(
            schemas.FlowNodeSchema(
                code=node.code,
                name=node.name,
                node_type=node.node_type,
                approval_mode=node.approval_mode,
                is_auto=node.is_auto,
                order=node.order,
                form_schema=strip_form_library(node.form_schema),
                groups=groups,
            )
        )

    transitions = [
        schemas.FlowTransitionSchema(
            source_code=t.source.code,
            target_code=t.target.code,
            condition_expr=t.condition_expr,
            description=t.description,
        )
        for t in FlowTransition.objects.filter(flow=flow_def).order_by("id")
    ]

    return schemas.FlowDefinitionDetailSchema(
        flow_id=flow_def.id,
        code=flow_def.code,
        name=flow_def.name,
        description=flow_def.description,
        is_active=flow_def.is_active,
        nodes=nodes,
        transitions=transitions,
        form_library=[],
    )


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "query flow definition detail failed"
    response_schema = schemas.FlowDefinitionDetailSchema
    error_codes = [
        ("001", "flow definition not found"),
    ]

    @staticmethod
    async def api(request: HttpRequest, flow_id: int = Query(..., description="flow id")):
        def _build_detail():
            flow_def = FlowDefinition.objects.filter(pk=flow_id).first()
            if not flow_def:
                raise BusinessException("001")
            return build_flow_definition_detail(flow_def)

        return await sync_to_async(_build_detail, thread_sensitive=True)()
