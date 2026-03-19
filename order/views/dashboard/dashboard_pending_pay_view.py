# -*-coding:utf-8 -*-
from asgiref.sync import sync_to_async

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.enums import OrderStatusChoices
from order.models import Order


class DashboardPendingPayView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询待收款订单失败"
    response_schema = list
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        def fetch_pending_pay():
            qs = (
                Order.objects
                .filter(is_delete=False)
                .select_related("site")
                .order_by("-update_time")[:10]
            )
            mapping = dict(OrderStatusChoices.choices)
            return [
                {
                    "id": obj.id,
                    "order_no": obj.order_no,
                    "site": obj.site.site_name if obj.site else "未分配站点",
                    "customer": getattr(obj, "receiver_name", "") or getattr(obj, "receiver_company", "") or "",
                    "amount": f"{obj.payable_amount:,.0f}",
                    "time": obj.update_time.strftime("%m-%d %H:%M") if obj.update_time else "",
                    "status": mapping.get(obj.order_status, str(obj.order_status)),
                }
                for obj in qs
            ]

        return await sync_to_async(fetch_pending_pay, thread_sensitive=True)()
