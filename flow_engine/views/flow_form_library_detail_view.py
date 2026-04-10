# -*-coding:utf-8 -*-

"""
# Description: query form library bound to flow definition
"""

from asgiref.sync import sync_to_async

from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import FlowDefinition, FlowNode
from flow_engine.utils.form_library_util import extract_form_library_from_nodes
from . import schemas


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "query flow form library failed"
    response_schema = schemas.FlowFormLibraryDetailSchema
    error_codes = [
        ("001", "flow definition not found"),
    ]

    @staticmethod
    async def api(request: HttpRequest, flow_id: int = Query(..., description="flow id")):
        def _query_detail():
            flow_def = FlowDefinition.objects.filter(pk=flow_id).first()
            if not flow_def:
                raise BusinessException("001")
            nodes = list(FlowNode.objects.filter(flow=flow_def).order_by("order", "id"))
            forms = extract_form_library_from_nodes(nodes)
            return schemas.FlowFormLibraryDetailSchema(
                flow_id=flow_def.id,
                code=flow_def.code,
                name=flow_def.name,
                forms=forms,
            )

        return await sync_to_async(_query_detail, thread_sensitive=True)()

