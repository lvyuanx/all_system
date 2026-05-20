# -*-coding:utf-8 -*-
from asgiref.sync import sync_to_async

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.enums import OrderStatusChoices
from order.models import Order
from site_mgmt.utils import site_util


class DashboardPendingShipView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询待发货订单失败"
    response_schema = list
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        def fetch_pending_ship():
            qs = (
                site_util.admin_filter_site(
                    request,
                    Order.objects.filter(
                        is_delete=False,
                        order_status=OrderStatusChoices.FINISHED,
                    ),
                )
                .select_related("site")
                .order_by("-create_time")[:10]
            )
            return [
                {
                    "id": obj.id,
                    "order_no": obj.order_no,
                    "site": obj.site.site_name if obj.site else "未分配站点",
                    "customer": getattr(obj, "receiver_name", "") or getattr(obj, "receiver_company", "") or "",
                    "amount": f"{obj.payable_amount:,.0f}",
                    "time": obj.create_time.strftime("%m-%d %H:%M") if obj.create_time else "",
                }
                for obj in qs
            ]

        return await sync_to_async(fetch_pending_ship, thread_sensitive=True)()
