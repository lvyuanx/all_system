# -*-coding:utf-8 -*-

"""
# File       : mobile_order_meta_view.py
# Description: 移动端订单元数据接口
"""

from asgiref.sync import sync_to_async
from core.common.schemas import ChoicesListItemSchema
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.utils.common_util import choices_to_schema
from order import enums
from order.models import Order
from site_mgmt.utils import site_util


class MobileOrderReceiverOptionsView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询收货方信息失败"
    response_schema = dict
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        qs = Order.objects.filter(is_delete=False).values(
            "receiver_name",
            "receiver_company",
            "site_id",
        )
        qs = await sync_to_async(site_util.admin_filter_site)(request, qs)

        name_set = set()
        company_set = set()
        pairs = set()
        async for item in qs:
            name = (item.get("receiver_name") or "").strip()
            company = (item.get("receiver_company") or "").strip()
            site_id = item.get("site_id")
            if name:
                name_set.add(name)
            if company:
                company_set.add(company)
            if site_id and (name or company):
                pairs.add((site_id, name or None, company or None))

        return {
            "receiver_names": sorted(name_set),
            "receiver_companies": sorted(company_set),
            "receiver_options": [
                {"site_id": sid, "receiver_name": rname, "receiver_company": rcompany}
                for (sid, rname, rcompany) in sorted(pairs, key=lambda x: (x[0], x[1] or "", x[2] or ""))
            ],
        }


class MobileOrderPayStatusAllListView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询订单支付状态失败"
    response_schema = list[ChoicesListItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return choices_to_schema(enums.OrderPayStatusChoices)


class MobileOrderShipStatusAllListView(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询订单发货状态失败"
    response_schema = list[ChoicesListItemSchema]
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return choices_to_schema(enums.OrderShipStatusChoices)
