# -*-coding:utf-8 -*-

"""
# Description: resolve runtime form schema/data by raw form schema (preview only)
"""

from asgiref.sync import sync_to_async

from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from flow_engine.utils.form_runtime_util import resolve_form_runtime
from flow_engine.utils.form_library_util import FORM_REF_CODE_KEY, FORM_REF_NAME_KEY, resolve_form_ref_definition

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "resolve flow runtime preview failed"
    response_schema = schemas.FlowFormRuntimePreviewResolveRespSchema

    @staticmethod
    def _strip_form_schema_ui(schema):
        if not isinstance(schema, dict):
            return schema
        cleaned = dict(schema)
        cleaned.pop("__ui", None)
        cleaned.pop("__form_library", None)
        return cleaned

    @staticmethod
    def _hydrate_form_schema(schema):
        if not isinstance(schema, dict):
            return schema
        ref_code = str(schema.get(FORM_REF_CODE_KEY) or "").strip()
        if not ref_code:
            return schema
        matched = resolve_form_ref_definition(ref_code)
        if not matched:
            return schema
        hydrated = {
            "fields": matched.get("fields") or [],
            FORM_REF_CODE_KEY: matched.get("code") or ref_code,
            FORM_REF_NAME_KEY: matched.get("name") or ref_code,
        }
        if "__ui" in schema:
            hydrated["__ui"] = schema["__ui"]
        return hydrated

    @staticmethod
    async def api(
        request: HttpRequest,
        data: schemas.FlowFormRuntimePreviewResolveSchema = Body(..., description="resolve preview runtime form"),
    ):
        raw_schema = View._hydrate_form_schema(View._strip_form_schema_ui(data.form_schema))
        context = data.context if isinstance(data.context, dict) else {}
        runtime_env = data.runtime_env if isinstance(data.runtime_env, dict) else {}
        node_code = str(data.node_code or "")

        resolved_schema, resolved_form_data = await sync_to_async(
            lambda: resolve_form_runtime(
                form_schema=raw_schema,
                context=context,
                node_code=node_code,
                runtime_env=runtime_env,
                request=request,
                instance=None,
            ),
            thread_sensitive=True,
        )()

        return schemas.FlowFormRuntimePreviewResolveRespSchema(
            resolved_form_schema=resolved_schema or {},
            resolved_form_data=resolved_form_data or {},
            context_snapshot=context,
        )
