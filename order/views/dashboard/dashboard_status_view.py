# -*-coding:utf-8 -*-
from asgiref.sync import sync_to_async
from django.db.models import Count

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.enums import OrderStatusChoices
from order.models import Order


class DashboardStatusView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘状态分布失败"
    response_schema = list
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        def calc_status():
            qs = (
                Order.objects
                .filter(is_delete=False)
                .values("order_status")
                .annotate(total=Count("id"))
                .order_by("order_status")
            )
            mapping = dict(OrderStatusChoices.choices)
            return [
                {"name": mapping.get(row["order_status"], str(row["order_status"])), "value": row["total"]}
                for row in qs
            ]

        return await sync_to_async(calc_status, thread_sensitive=True)()
