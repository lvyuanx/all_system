# -*-coding:utf-8 -*-

"""
# Description: export flow definition json
"""

from asgiref.sync import sync_to_async
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import FlowDefinition
from . import schemas
from .flow_definition_detail_view import build_flow_definition_detail


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "export flow definition failed"
    response_schema = schemas.FlowDefinitionSaveSchema
    error_codes = [
        ("001", "flow definition not found"),
    ]

    @staticmethod
    async def api(request: HttpRequest, flow_id: int = Query(..., description="flow id")):
        def _export():
            flow_def = FlowDefinition.objects.filter(pk=flow_id).first()
            if not flow_def:
                raise BusinessException("001")
            detail = build_flow_definition_detail(flow_def)
            return schemas.FlowDefinitionSaveSchema(
                flow_id=detail.flow_id,
                code=detail.code,
                name=detail.name,
                description=detail.description,
                is_active=detail.is_active,
                nodes=detail.nodes,
                transitions=detail.transitions,
            )

        return await sync_to_async(_export, thread_sensitive=True)()
