# -*-coding:utf-8 -*-

"""
# Description: save flow definition for designer
"""

from asgiref.sync import sync_to_async
from django.db import transaction

from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import (
    FlowDefinition,
    FlowNode,
    FlowTransition,
    FlowNodeGroup,
    FlowNodeGroupRule,
)
from flow_engine.enums import NodeTypeChoices
from . import schemas


def save_flow_definition(data: schemas.FlowDefinitionSaveSchema) -> dict:
    if not data.nodes:
        raise BusinessException("002")

    codes = [n.code for n in data.nodes]
    if len(set(codes)) != len(codes):
        raise BusinessException("003")

    start_count = len([n for n in data.nodes if n.node_type == NodeTypeChoices.START])
    if start_count != 1:
        raise BusinessException("004")

    if data.flow_id:
        if FlowDefinition.objects.filter(code=data.code).exclude(pk=data.flow_id).exists():
            raise BusinessException("005")
    else:
        if FlowDefinition.objects.filter(code=data.code).exists():
            raise BusinessException("005")

    with transaction.atomic():
        if data.flow_id:
            flow_def = FlowDefinition.objects.filter(pk=data.flow_id).first()
            if not flow_def:
                raise BusinessException("001")
        else:
            flow_def = FlowDefinition.objects.create(
                code=data.code,
                name=data.name,
                description=data.description,
                is_active=data.is_active,
            )

        flow_def.code = data.code
        flow_def.name = data.name
        flow_def.description = data.description
        flow_def.is_active = data.is_active
        flow_def.save()

        FlowTransition.objects.filter(flow=flow_def).delete()
        FlowNodeGroupRule.objects.filter(group__node__flow=flow_def).delete()
        FlowNodeGroup.objects.filter(node__flow=flow_def).delete()
        FlowNode.objects.filter(flow=flow_def).delete()

        node_map = {}
        for idx, node in enumerate(data.nodes):
            node_obj = FlowNode.objects.create(
                flow=flow_def,
                code=node.code,
                name=node.name,
                node_type=node.node_type,
                approval_mode=node.approval_mode,
                is_auto=node.is_auto,
                order=node.order if node.order is not None else idx,
                form_schema=node.form_schema,
            )
            node_map[node.code] = node_obj

            for g_idx, group in enumerate(node.groups or []):
                group_obj = FlowNodeGroup.objects.create(
                    node=node_obj,
                    key=group.key,
                    name=group.name,
                    min_approve_count=group.min_approve_count,
                    order=group.order if group.order is not None else g_idx,
                )
                for rule in group.rules or []:
                    if rule.rule_type == "perm_pack" and not rule.perm_pack_id:
                        continue
                    if rule.rule_type == "user" and not rule.user_id:
                        continue
                    FlowNodeGroupRule.objects.create(
                        group=group_obj,
                        rule_type=rule.rule_type,
                        perm_pack_id=rule.perm_pack_id,
                        user_id=rule.user_id,
                    )

        for trans in data.transitions or []:
            if trans.source_code not in node_map or trans.target_code not in node_map:
                raise BusinessException("006")
            FlowTransition.objects.create(
                flow=flow_def,
                source=node_map[trans.source_code],
                target=node_map[trans.target_code],
                condition_expr=trans.condition_expr,
                description=trans.description,
            )

    return {"flow_id": flow_def.id}


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "save flow definition failed"
    response_schema = schemas.FlowDefinitionActionRespSchema
    error_codes = [
        ("001", "flow definition not found"),
        ("002", "at least one node required"),
        ("003", "duplicate node code"),
        ("004", "must have exactly one start node"),
        ("005", "flow code already exists"),
        ("006", "transition node not found"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.FlowDefinitionSaveSchema = Body(...)):
        return await sync_to_async(save_flow_definition, thread_sensitive=True)(data)
