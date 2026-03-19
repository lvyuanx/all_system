# -*-coding:utf-8 -*-
from asgiref.sync import sync_to_async
from django.db.models import Sum

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.models import Order


class DashboardSiteTopView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘站点Top失败"
    response_schema = list
    error_codes = []

    @staticmethod
    def _to_wan(val):
        return round(float(val or 0) / 10000, 2)

    @staticmethod
    async def api(request: HttpRequest):
        def calc_site_top():
            qs = (
                Order.objects
                .filter(is_delete=False, site__isnull=False)
                .values("site", "site__site_name")
                .annotate(total=Sum("payable_amount"))
                .order_by("-total")[:5]
            )
            return [
                {
                    "name": row.get("site__site_name") or "未分配站点",
                    "value": DashboardSiteTopView._to_wan(row.get("total")),
                }
                for row in qs
            ]

        return await sync_to_async(calc_site_top, thread_sensitive=True)()
