# -*-coding:utf-8 -*-
from datetime import timedelta
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db.models import Sum
from django.utils import timezone

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.enums import OrderShipStatusChoices, OrderPayStatusChoices
from order.models import Order
from site_mgmt.utils import site_util


class DashboardSummaryView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘汇总失败"
    response_schema = dict
    error_codes = []

    @staticmethod
    def _to_number(val: Decimal | None) -> float:
        return float(val or 0)

    @staticmethod
    def _time_ranges(now):
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        yesterday_start = today_start - timedelta(days=1)
        # 本月起始和下个月起始
        if today_start.month == 12:
            next_month_start = today_start.replace(year=today_start.year + 1, month=1, day=1)
        else:
            next_month_start = today_start.replace(month=today_start.month + 1, day=1)
        month_start = today_start.replace(day=1)
        return today_start, tomorrow_start, yesterday_start, month_start, next_month_start

    @staticmethod
    async def api(request: HttpRequest):
        # 在异步视图中调用同步 ORM，需用 sync_to_async 包装
        def calc_summary():
            now = timezone.localtime()
            today_start, tomorrow_start, yesterday_start, month_start, next_month_start = (
                DashboardSummaryView._time_ranges(now)
            )

            base_qs = site_util.admin_filter_site(request, Order.objects.filter(is_delete=False))

            today_qs = base_qs.filter(create_time__gte=today_start, create_time__lt=tomorrow_start)
            today_order_count = today_qs.count()
            today_amount = today_qs.aggregate(val=Sum("payable_amount"))['val'] or Decimal("0")

            yesterday_qs = base_qs.filter(create_time__gte=yesterday_start, create_time__lt=today_start)
            yesterday_order_count = yesterday_qs.count()
            yesterday_amount = yesterday_qs.aggregate(val=Sum("payable_amount"))['val'] or Decimal("0")

            today_order_delta = today_order_count - yesterday_order_count
            if yesterday_amount > 0:
                today_amount_delta_rate = round((today_amount - yesterday_amount) / yesterday_amount * 100, 2)
            else:
                today_amount_delta_rate = 0

            pending_ship = base_qs.filter(
                ship_status__in=[
                    OrderShipStatusChoices.NOT_SHIPPED,
                    OrderShipStatusChoices.PARTIAL_SHIPMENT,
                ]
            ).count()
            pending_pay = base_qs.filter(
                pay_status__in=[
                    OrderPayStatusChoices.NOT_PAID,
                    OrderPayStatusChoices.PAID_PARTIAL,
                ]
            ).count()

            month_amount = base_qs.filter(
                create_time__gte=month_start,
                create_time__lt=next_month_start,
            ).aggregate(val=Sum("payable_amount"))['val'] or Decimal("0")

            new_customer = 0

            return {
                "today_order_count": today_order_count,
                "today_order_delta": today_order_delta,
                "today_amount": DashboardSummaryView._to_number(today_amount),
                "today_amount_delta_rate": today_amount_delta_rate,
                "pending_ship": pending_ship,
                "pending_pay": pending_pay,
                "month_amount": DashboardSummaryView._to_number(month_amount),
                "new_customer": new_customer,
            }

        return await sync_to_async(calc_summary, thread_sensitive=True)()
