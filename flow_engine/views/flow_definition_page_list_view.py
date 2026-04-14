# -*-coding:utf-8 -*-

"""
# Description: 流程列表（设计器页面使用）
"""

from asgiref.sync import sync_to_async
from django.db import models

from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.utils import time_util

from flow_engine.models import FlowDefinition
from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询流程列表失败"
    response_schema = list[schemas.FlowDefinitionListItemSchema]
    error_codes = []

    @staticmethod
    async def api(
        request: HttpRequest,
        keyword: str | None = Query(None, description="关键字"),
        is_active: int | None = Query(None, description="是否启用(1/0)"),
    ):
        def _query():
            qs = FlowDefinition.objects.all()
            if keyword:
                qs = qs.filter(
                    models.Q(code__icontains=keyword)
                    | models.Q(name__icontains=keyword)
                )
            if is_active in (0, 1):
                qs = qs.filter(is_active=bool(is_active))
            qs = qs.annotate(
                bind_order_count=models.Count(
                    "order",
                    filter=models.Q(order__is_delete=False),
                    distinct=True,
                )
            )
            return list(qs.order_by("-update_time", "-id"))

        rows = await sync_to_async(_query, thread_sensitive=True)()
        return [
            schemas.FlowDefinitionListItemSchema(
                flow_id=row.id,
                code=row.code,
                name=row.name,
                version=row.version,
                is_active=row.is_active,
                bind_order_count=getattr(row, "bind_order_count", 0) or 0,
                create_time_str=time_util.datetime_to_str(row.create_time) if row.create_time else None,
                update_time_str=time_util.datetime_to_str(row.update_time) if row.update_time else None,
            )
            for row in rows
        ]
