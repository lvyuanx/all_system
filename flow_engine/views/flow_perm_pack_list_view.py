# -*-coding:utf-8 -*-

"""
# Description: 权限包列表
"""

from asgiref.sync import sync_to_async
from core.ninja_extra.api_extra import BaseApi, HttpRequest

from core.auth.models import PermissionPack
from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询权限包失败"
    response_schema = list[schemas.FlowPermPackItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        packs = await sync_to_async(list)(
            PermissionPack.objects.all().order_by("pack_code").values(
                "id", "pack_code", "pack_name"
            )
        )
        return [
            schemas.FlowPermPackItemSchema(
                pack_id=row["id"], pack_code=row["pack_code"], pack_name=row["pack_name"]
            )
            for row in packs
        ]
