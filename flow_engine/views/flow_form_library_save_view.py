# -*-coding:utf-8 -*-

"""
# Description: save flow form library
"""

from asgiref.sync import sync_to_async
from copy import deepcopy
from django.db import transaction

from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.exceptions.base_exceptions import BusinessException

from flow_engine.enums import NodeTypeChoices
from flow_engine.models import FlowDefinition, FlowNode
from flow_engine.utils.form_library_util import (
    inject_form_library,
    normalize_form_library,
    strip_form_library,
    FORM_REF_CODE_KEY,
    FORM_REF_NAME_KEY,
)
from . import schemas


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "save flow form library failed"
    response_schema = schemas.FlowFormLibraryDetailSchema
    error_codes = [
        ("001", "flow definition not found"),
        ("002", "flow nodes not found"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.FlowFormLibrarySaveSchema = Body(...)):
        def _save_detail():
            flow_def = FlowDefinition.objects.filter(pk=data.flow_id).first()
            if not flow_def:
                raise BusinessException("001")

            nodes = list(FlowNode.objects.filter(flow=flow_def).order_by("order", "id"))
            if not nodes:
                raise BusinessException("002")

            host_node = next(
                (node for node in nodes if node.node_type == NodeTypeChoices.START),
                nodes[0],
            )
            forms = normalize_form_library(
                [
                    item.dict() if hasattr(item, "dict") else item
                    for item in (data.forms or [])
                ]
            )
            forms_map = {item["code"]: item for item in forms}

            with transaction.atomic():
                for node in nodes:
                    raw_schema = node.form_schema if isinstance(node.form_schema, dict) else {}
                    next_schema = deepcopy(raw_schema)
                    ref_code = (next_schema or {}).get(FORM_REF_CODE_KEY) if isinstance(next_schema, dict) else None
                    if ref_code and ref_code in forms_map:
                        ui_state = next_schema.get("__ui") if isinstance(next_schema, dict) else None
                        matched = forms_map[ref_code]
                        next_schema = {
                            "fields": deepcopy(matched.get("fields") or []),
                            FORM_REF_CODE_KEY: matched["code"],
                            FORM_REF_NAME_KEY: matched.get("name") or matched["code"],
                        }
                        if ui_state:
                            next_schema["__ui"] = ui_state

                    if node.id == host_node.id:
                        next_schema = inject_form_library(next_schema, forms)
                    else:
                        next_schema = strip_form_library(next_schema)
                    if node.form_schema != next_schema:
                        node.form_schema = next_schema
                        node.save(update_fields=["form_schema"])

            return schemas.FlowFormLibraryDetailSchema(
                flow_id=flow_def.id,
                code=flow_def.code,
                name=flow_def.name,
                forms=forms,
            )

        return await sync_to_async(_save_detail, thread_sensitive=True)()
