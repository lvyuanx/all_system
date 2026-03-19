# -*-coding:utf-8 -*-
from asgiref.sync import sync_to_async
from django.db.models import Count

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.enums import OrderTypeChoices
from order.models import Order


class DashboardTypeView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘订单类型失败"
    response_schema = list
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        def calc_type():
            qs = (
                Order.objects
                .filter(is_delete=False)
                .values("order_type")
                .annotate(total=Count("id"))
                .order_by("order_type")
            )
            mapping = dict(OrderTypeChoices.choices)
            return [
                {"name": mapping.get(row["order_type"], str(row["order_type"])), "value": row["total"]}
                for row in qs
            ]

        return await sync_to_async(calc_type, thread_sensitive=True)()
