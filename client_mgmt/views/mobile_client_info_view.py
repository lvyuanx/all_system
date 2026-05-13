# -*-coding:utf-8 -*-

"""
# File       : mobile_client_info_view.py
# Description: 移动端查询客户详情（只读）
"""

from decimal import Decimal

from django.db.models import F

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from core.utils import common_util
from client_mgmt.models import Client
from site_mgmt.utils import site_util

from . import schemas


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "移动端查询客户详情失败"
    response_schema = schemas.MobileClientInfoSchema
    error_codes = [
        ("001", "未查询到客户信息"),
        ("002", "暂无该客户查看权限"),
    ]

    @staticmethod
    async def api(request: HttpRequest, client_id: int = Query(..., description="客户ID")):
        base_manager = Client.objects.filter(pk=client_id, is_active=True)
        if not await base_manager.aexists():
            raise BusinessException("001")

        cur_user = await common_util.get_user_async(request)
        manager = base_manager
        if not cur_user.is_superuser:
            sites = await site_util.aget_cur_sites(request)
            site_ids = [s.pk for s in sites]
            if not site_ids:
                raise BusinessException("002")
            manager = manager.filter(sites__in=site_ids)

        if not await manager.aexists():
            raise BusinessException("002")

        client_obj = await manager.distinct().values(
            "client_name",
            "client_phone",
            "client_sex",
            "client_age",
            "settlement_method",
            "company_name",
            "company_phone",
            "address_province__name",
            "address_city__name",
            "address_district__name",
            "address_detail",
            "total_amount",
            "total_arrears",
            "total_order_count",
            "total_end_order_count",
            company_logo_file=F("company_logo"),
            client_id=F("pk"),
        ).afirst()

        if client_obj is None:
            raise BusinessException("001")

        sex = client_obj.get("client_sex") or Client.Gender.UNKNOWN
        try:
            sex_str = Client.Gender(sex).label
        except Exception:
            sex_str = ""
        settlement_method = client_obj.get("settlement_method") or Client.SettlementMethod.MONTHLY
        try:
            settlement_method_str = Client.SettlementMethod(settlement_method).label
        except Exception:
            settlement_method_str = ""

        province = client_obj.get("address_province__name", "") or ""
        city = client_obj.get("address_city__name", "") or ""
        district = client_obj.get("address_district__name", "") or ""
        detail = client_obj.get("address_detail", "") or ""
        total_order_count = int(client_obj.get("total_order_count") or 0)
        total_end_order_count = int(client_obj.get("total_end_order_count") or 0)

        site_names = [
            site_name
            async for site_name in manager.values_list("sites__site_name", flat=True)
            if site_name
        ]

        return schemas.MobileClientInfoSchema(
            client_id=client_obj["client_id"],
            client_name=client_obj.get("client_name", ""),
            client_phone=client_obj.get("client_phone"),
            client_sex=sex,
            client_sex_str=sex_str,
            client_age=client_obj.get("client_age"),
            settlement_method=settlement_method,
            settlement_method_str=settlement_method_str,
            company_name=client_obj.get("company_name"),
            company_phone=client_obj.get("company_phone"),
            company_logo=common_util.media_url(client_obj.get("company_logo_file", "")),
            address_province=province or None,
            address_city=city or None,
            address_district=district or None,
            address_detail=detail or None,
            full_address=province + city + district + detail,
            total_amount=float(client_obj.get("total_amount") or Decimal("0")),
            total_arrears=float(client_obj.get("total_arrears") or Decimal("0")),
            total_order_count=total_order_count,
            total_end_order_count=total_end_order_count,
            unfinished_order_total=total_order_count - total_end_order_count,
            site_names=list(dict.fromkeys(site_names)),
        )
