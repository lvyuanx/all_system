# -*-coding:utf-8 -*-
from datetime import timedelta
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.models import Order


class DashboardTrendView(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询仪表盘趋势失败"
    response_schema = dict
    error_codes = []

    @staticmethod
    def _to_wan(val: Decimal | None) -> float:
        return round(float(val or 0) / 10000, 2)

    @staticmethod
    def _today_range(now):
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        return today_start, tomorrow_start

    @staticmethod
    def _build_daily(base_qs, start_dt, end_dt):
        agg = (
            base_qs.filter(create_time__gte=start_dt, create_time__lt=end_dt)
            .annotate(day=TruncDate("create_time"))
            .values("day")
            .annotate(cnt=Count("id"), amt=Sum("payable_amount"))
            .order_by("day")
        )
        mapping = {r["day"]: r for r in agg}
        total_days = (end_dt - start_dt).days
        xs, counts, amounts = [], [], []
        for i in range(total_days):
            d = start_dt + timedelta(days=i)
            xs.append(d.strftime("%m-%d"))
            row = mapping.get(d.date())
            counts.append(row["cnt"] if row else 0)
            amounts.append(DashboardTrendView._to_wan(row["amt"]) if row else 0)
        return {"x": xs, "count": counts, "amount": amounts}

    @staticmethod
    def _build_weekly(base_qs, start_dt, end_dt):
        agg = (
            base_qs.filter(create_time__gte=start_dt, create_time__lt=end_dt)
            .annotate(week=TruncWeek("create_time"))
            .values("week")
            .annotate(cnt=Count("id"), amt=Sum("payable_amount"))
            .order_by("week")
        )
        xs, counts, amounts = [], [], []
        for idx, row in enumerate(agg, start=1):
            xs.append(f"第{idx}周")
            counts.append(row["cnt"] or 0)
            amounts.append(DashboardTrendView._to_wan(row["amt"]))
        return {"x": xs, "count": counts, "amount": amounts}

    @staticmethod
    async def api(request: HttpRequest):
        # 在异步视图中调用同步 ORM，需用 sync_to_async 包装
        def calc_trend():
            now = timezone.localtime()
            today_start, tomorrow_start = DashboardTrendView._today_range(now)

            start_7 = today_start - timedelta(days=6)
            start_30 = today_start - timedelta(days=29)
            start_90 = today_start - timedelta(days=89)

            base_qs = Order.objects.filter(is_delete=False)

            trend_7 = DashboardTrendView._build_daily(base_qs, start_7, tomorrow_start)
            trend_30 = DashboardTrendView._build_daily(base_qs, start_30, tomorrow_start)
            trend_90 = DashboardTrendView._build_weekly(base_qs, start_90, tomorrow_start)

            return {
                "7": trend_7,
                "30": trend_30,
                "90": trend_90,
            }

        return await sync_to_async(calc_trend, thread_sensitive=True)()
