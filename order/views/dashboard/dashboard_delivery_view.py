# -*-coding:utf-8 -*-
from asgiref.sync import sync_to_async
from django.db.models import Count

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.enums import OrderDeliveryChoices
from order.models import Order
from site_mgmt.utils import site_util


class DashboardDeliveryView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘配送方式失败"
    response_schema = list
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        def calc_delivery():
            qs = (
                site_util.admin_filter_site(request, Order.objects.filter(is_delete=False))
                .values("delivery_method")
                .annotate(total=Count("id"))
                .order_by("delivery_method")
            )
            mapping = dict(OrderDeliveryChoices.choices)
            return [
                {"name": mapping.get(row["delivery_method"], str(row["delivery_method"])), "value": row["total"]}
                for row in qs
            ]

        return await sync_to_async(calc_delivery, thread_sensitive=True)()
