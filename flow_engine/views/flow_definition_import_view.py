# -*-coding:utf-8 -*-

"""
# Description: import flow definition json
"""

from asgiref.sync import sync_to_async
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import FlowDefinition
from . import schemas
from .flow_definition_save_view import save_flow_definition


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "import flow definition failed"
    response_schema = schemas.FlowDefinitionActionRespSchema
    error_codes = [
        ("001", "flow definition code already exists"),
        ("002", "flow definition not found"),
        ("003", "at least one node required"),
        ("004", "duplicate node code"),
        ("005", "must have exactly one start node"),
        ("006", "flow code already exists"),
        ("007", "transition node not found"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.FlowDefinitionImportSchema = Body(...)):
        def _import():
            payload_data = data.payload.dict()
            payload_data["flow_id"] = None  # ignore source env flow_id by default
            payload = schemas.FlowDefinitionSaveSchema(**payload_data)

            existing = FlowDefinition.objects.filter(code=payload.code).first()
            if existing and not data.overwrite:
                raise BusinessException("001")
            if existing and data.overwrite:
                payload.flow_id = existing.id
            try:
                return save_flow_definition(payload)
            except BusinessException as exc:
                # Remap save codes (001-006) to import view codes (002-007)
                mapping = {
                    "001": "002",
                    "002": "003",
                    "003": "004",
                    "004": "005",
                    "005": "006",
                    "006": "007",
                }
                remapped = mapping.get(exc.error_code, None)
                if remapped:
                    raise BusinessException(remapped, exc.data)
                raise

        return await sync_to_async(_import, thread_sensitive=True)()
