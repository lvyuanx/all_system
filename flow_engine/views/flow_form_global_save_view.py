# -*-coding:utf-8 -*-

"""
# Description: save global form library
"""

from asgiref.sync import sync_to_async
from django.db import transaction

from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from core.exceptions.base_exceptions import BusinessException

from flow_engine.models import FlowForm, FlowNode
from flow_engine.utils.form_library_util import FORM_REF_CODE_KEY, normalize_form_library
from . import schemas


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "save global form library failed"
    response_schema = schemas.GlobalFormLibraryDetailSchema
    error_codes = [
        ("001", "form code already exists"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.GlobalFormLibrarySaveSchema = Body(...)):
        def _save():
            forms = normalize_form_library(
                [item.dict() if hasattr(item, "dict") else item for item in (data.forms or [])]
            )
            payload_codes = {item["code"] for item in forms}
            existing = {item.code: item for item in FlowForm.objects.all()}

            referenced_codes: set[str] = set()
            for node in FlowNode.objects.all().only("form_schema"):
                schema = node.form_schema if isinstance(node.form_schema, dict) else {}
                ref_code = str(schema.get(FORM_REF_CODE_KEY) or "").strip()
                if ref_code:
                    referenced_codes.add(ref_code)

            with transaction.atomic():
                for code, item in existing.items():
                    if code in payload_codes:
                        continue
                    if code in referenced_codes:
                        # Keep referenced forms even if they are absent in payload.
                        # This avoids failing the entire save when payload is partial
                        # or when a referenced form is removed by mistake.
                        continue
                    item.delete()

                for item in forms:
                    form_obj = existing.get(item["code"])
                    form_schema = {"fields": item.get("fields") or []}
                    if form_obj is None:
                        if FlowForm.objects.filter(code=item["code"]).exists():
                            raise BusinessException("001")
                        FlowForm.objects.create(
                            code=item["code"],
                            name=item["name"],
                            group_name=item.get("group_name") or "",
                            description=item.get("description") or "",
                            form_schema=form_schema,
                            is_active=True,
                        )
                    else:
                        form_obj.name = item["name"]
                        form_obj.group_name = item.get("group_name") or ""
                        form_obj.description = item.get("description") or ""
                        form_obj.form_schema = form_schema
                        form_obj.save(update_fields=["name", "group_name", "description", "form_schema", "update_time"])

            result = []
            for item in FlowForm.objects.all().order_by("group_name", "code", "-update_time"):
                schema = item.form_schema if isinstance(item.form_schema, dict) else {}
                fields = schema.get("fields") if isinstance(schema.get("fields"), list) else []
                result.append(
                    schemas.FlowFormDefinitionSchema(
                        code=item.code,
                        name=item.name,
                        group_name=item.group_name or None,
                        description=item.description,
                        fields=fields,
                        order=0,
                    )
                )
            return schemas.GlobalFormLibraryDetailSchema(forms=result)

        return await sync_to_async(_save, thread_sensitive=True)()
