# -*-coding:utf-8 -*-

"""
# Description: 用户列表（用于流程节点指定人）
"""

from asgiref.sync import sync_to_async
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from django.db import models

from core.auth.models import User
from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询用户失败"
    response_schema = list[schemas.FlowUserItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest, keyword: str | None = Query(None, description="关键词")):
        def _query():
            qs = User.objects.filter(is_active=True)
            if keyword:
                qs = qs.filter(
                    models.Q(full_name__icontains=keyword)
                    | models.Q(username__icontains=keyword)
                    | models.Q(phone__icontains=keyword)
                )
            return list(
                qs.order_by("id")
                .values("id", "full_name", "phone")[:50]
            )

        rows = await sync_to_async(_query, thread_sensitive=True)()
        return [
            schemas.FlowUserItemSchema(
                user_id=row["id"],
                full_name=row["full_name"],
                phone=row["phone"],
            )
            for row in rows
        ]
