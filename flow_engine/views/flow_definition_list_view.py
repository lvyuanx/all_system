# -*-coding:utf-8 -*-

"""
# Description: 查询可用流程模板列表
"""

from asgiref.sync import sync_to_async
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.common.schemas import ChoicesListItemSchema
from flow_engine.models import FlowDefinition
from flow_engine.enums import FlowVersionStatusChoices


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询流程模板失败"
    response_schema = list[ChoicesListItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        rows = await sync_to_async(list)(
            FlowDefinition.objects.filter(
                is_active=True, versions__status=FlowVersionStatusChoices.PUBLISHED
            )
            .distinct()
            .values("id", "code", "name")
            .order_by("id")
        )
        return [
            ChoicesListItemSchema(label=row["name"], name=row["code"], value=row["id"])
            for row in rows
        ]
