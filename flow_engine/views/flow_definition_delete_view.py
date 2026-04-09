# -*-coding:utf-8 -*-

"""
# Description: delete flow definition
"""

from asgiref.sync import sync_to_async
from django.apps import apps
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import FlowDefinition
from . import schemas


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "delete flow definition failed"
    response_schema = schemas.FlowDefinitionActionRespSchema
    error_codes = [
        ("001", "flow definition not found"),
        ("002", "flow has bound orders, cannot delete"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.FlowDefinitionDeleteSchema = Body(...)):
        def _delete():
            flow_def = FlowDefinition.objects.filter(pk=data.flow_id).first()
            if not flow_def:
                raise BusinessException("001")

            Order = apps.get_model("order", "Order")
            if Order.objects.filter(flow_definition_id=flow_def.id, is_delete=False).exists():
                raise BusinessException("002")

            flow_id = flow_def.id
            flow_def.delete()
            return {"flow_id": flow_id}

        return await sync_to_async(_delete, thread_sensitive=True)()
