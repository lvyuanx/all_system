# -*-coding:utf-8 -*-

"""
# File       : mobile_order_create_view.py
# Description: 移动端创建订单
"""

from asgiref.sync import sync_to_async
from ninja import Body

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.views.order_create_view import do_create
from flow_engine.models import FlowDefinition
from flow_engine.enums import FlowVersionStatusChoices
from site_mgmt.utils import site_util

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "移动端创建订单失败"
    response_schema = None
    error_codes = [
        ("001", "请最少添加一个订单项"),
        ("002", "您没有该站点的订单创建权限"),
        ("003", "流程模板不存在或已停用"),
    ]

    @staticmethod
    async def api(request: HttpRequest, data: schemas.OrderCreateSchema = Body(...)):
        if not data.items:
            raise BusinessException("001")

        if data.flow_definition_id:
            exists = await sync_to_async(
                FlowDefinition.objects.filter(
                    pk=data.flow_definition_id,
                    is_active=True,
                    versions__status=FlowVersionStatusChoices.PUBLISHED,
                ).exists
            )()
            if not exists:
                raise BusinessException("003")

        cur_sites = await site_util.aget_cur_sites(request)
        if data.site_id not in [item.pk for item in cur_sites]:
            raise BusinessException("002")

        await sync_to_async(do_create)(data=data, request=request)
