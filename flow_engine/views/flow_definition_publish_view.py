# -*-coding:utf-8 -*-

"""
# Description: 发布流程版本
"""

from asgiref.sync import sync_to_async
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import FlowDefinition
from flow_engine.flow_engine import FlowEngine, FlowEngineError
from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "发布流程失败"
    response_schema = schemas.FlowDefinitionActionRespSchema
    error_codes = [
        ("001", "流程不存在"),
        ("002", "流程发布失败"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: dict = Body(..., description="flow_id")):
        flow_id = data.get("flow_id")
        if not flow_id:
            raise BusinessException("001")

        def _publish():
            flow_def = FlowDefinition.objects.filter(pk=flow_id).first()
            if not flow_def:
                raise BusinessException("001")
            try:
                FlowEngine.publish_definition(flow_def, published_by=request.user)
            except FlowEngineError:
                raise BusinessException("002")
            return {"flow_id": flow_def.id}

        return await sync_to_async(_publish, thread_sensitive=True)()
