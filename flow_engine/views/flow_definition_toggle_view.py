# -*-coding:utf-8 -*-

"""
# Description: 启用/禁用流程
"""

from asgiref.sync import sync_to_async
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import FlowDefinition
from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "更新流程状态失败"
    response_schema = schemas.FlowDefinitionActionRespSchema
    error_codes = [
        ("001", "流程不存在"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.FlowDefinitionToggleSchema = Body(...)):
        def _toggle():
            flow_def = FlowDefinition.objects.filter(pk=data.flow_id).first()
            if not flow_def:
                raise BusinessException("001")
            flow_def.is_active = data.is_active
            flow_def.save(update_fields=["is_active"])
            return {"flow_id": flow_def.id}

        return await sync_to_async(_toggle, thread_sensitive=True)()
