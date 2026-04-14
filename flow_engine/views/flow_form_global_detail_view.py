# -*-coding:utf-8 -*-

"""
# Description: query global form library detail
"""

from asgiref.sync import sync_to_async

from core.ninja_extra.api_extra import BaseApi, HttpRequest

from flow_engine.models import FlowForm
from . import schemas


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "query global form library detail failed"
    response_schema = schemas.GlobalFormLibraryDetailSchema
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        def _query():
            forms = []
            for item in FlowForm.objects.all().order_by("group_name", "code", "-update_time"):
                schema = item.form_schema if isinstance(item.form_schema, dict) else {}
                fields = schema.get("fields") if isinstance(schema.get("fields"), list) else []
                forms.append(
                    schemas.FlowFormDefinitionSchema(
                        code=item.code,
                        name=item.name,
                        group_name=item.group_name or None,
                        description=item.description,
                        fields=fields,
                        order=0,
                    )
                )
            return schemas.GlobalFormLibraryDetailSchema(forms=forms)

        return await sync_to_async(_query, thread_sensitive=True)()
