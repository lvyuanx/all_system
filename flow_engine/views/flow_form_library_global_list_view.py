# -*-coding:utf-8 -*-

"""
# Description: query global form library list
"""

from asgiref.sync import sync_to_async
from django.db.models import Q

from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.utils import time_util

from flow_engine.models import FlowForm, FlowNode
from flow_engine.utils.form_library_util import FORM_REF_CODE_KEY
from . import schemas


def _build_form_bind_metrics() -> tuple[dict[str, int], dict[str, set[int]]]:
    bind_node_counts: dict[str, int] = {}
    bind_flow_ids: dict[str, set[int]] = {}
    for node in FlowNode.objects.all().only("flow_id", "form_schema"):
        schema = node.form_schema if isinstance(node.form_schema, dict) else {}
        ref_code = str(schema.get(FORM_REF_CODE_KEY) or "").strip()
        if not ref_code:
            continue
        bind_node_counts[ref_code] = bind_node_counts.get(ref_code, 0) + 1
        bind_flow_ids.setdefault(ref_code, set()).add(node.flow_id)
    return bind_node_counts, bind_flow_ids


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "query global form library list failed"
    response_schema = list[schemas.GlobalFormLibraryItemSchema]
    error_codes = []

    @staticmethod
    async def api(
        request: HttpRequest,
        keyword: str | None = Query(None, description="keyword"),
        group_name: str | None = Query(None, description="form group name"),
    ):
        def _query():
            qs = FlowForm.objects.all().order_by("group_name", "code", "-update_time")
            if keyword:
                qs = qs.filter(
                    Q(code__icontains=keyword)
                    | Q(name__icontains=keyword)
                    | Q(group_name__icontains=keyword)
                    | Q(description__icontains=keyword)
                )
            if group_name:
                qs = qs.filter(group_name=group_name)

            bind_node_counts, bind_flow_ids = _build_form_bind_metrics()
            rows = []
            for item in qs:
                schema = item.form_schema if isinstance(item.form_schema, dict) else {}
                fields = schema.get("fields") if isinstance(schema.get("fields"), list) else []
                rows.append(
                    schemas.GlobalFormLibraryItemSchema(
                        form_id=item.id,
                        code=item.code,
                        name=item.name,
                        group_name=item.group_name or None,
                        description=item.description,
                        fields=fields,
                        order=0,
                        bind_flow_count=len(bind_flow_ids.get(item.code, set())),
                        bind_node_count=bind_node_counts.get(item.code, 0),
                        field_count=len(fields),
                        is_active=item.is_active,
                        update_time_str=time_util.datetime_to_str(item.update_time) if item.update_time else None,
                    )
                )
            return rows

        return await sync_to_async(_query, thread_sensitive=True)()
