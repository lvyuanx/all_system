# -*-coding:utf-8 -*-

"""
# File       : order_workflow_action_view.py
# Description: 订单流程审批动作
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from order.models import Order
from site_mgmt.utils import site_util
from flow_engine.flow_engine import FlowEngine, FlowEngineError
from flow_engine.enums import FlowStatusChoices
from flow_engine.utils.form_library_util import FORM_REF_CODE_KEY, FORM_REF_NAME_KEY, resolve_form_ref_definition
from flow_engine.utils.form_runtime_util import build_context_updates_from_form_data

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "订单流程操作失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单未绑定运行中的流程"),
        ("003", "当前用户在该流程节点没有可操作任务"),
        ("004", "不支持的流程操作"),
    ]

    @staticmethod
    def _strip_form_schema_ui(schema):
        if not isinstance(schema, dict):
            return schema
        cleaned = dict(schema)
        cleaned.pop("__ui", None)
        cleaned.pop("__form_library", None)
        return cleaned

    @staticmethod
    def _hydrate_form_schema(schema, node=None):
        if not isinstance(schema, dict):
            return schema
        ref_code = str(schema.get(FORM_REF_CODE_KEY) or "").strip()
        if not ref_code:
            return schema
        matched = resolve_form_ref_definition(ref_code, node)
        if not matched:
            return schema
        hydrated = {
            "fields": matched.get("fields") or [],
            FORM_REF_CODE_KEY: matched.get("code") or ref_code,
            FORM_REF_NAME_KEY: matched.get("name") or ref_code,
        }
        if "__ui" in schema:
            hydrated["__ui"] = schema["__ui"]
        return hydrated

    @staticmethod
    async def api(
        request: HttpRequest,
        data: schemas.OrderWorkflowActionSchema = Body(..., description="订单流程操作"),
    ):
        order_manager = Order.objects.filter(pk=data.order_id, is_delete=False)
        order_manager = await sync_to_async(site_util.admin_filter_site)(request, order_manager)
        if not await order_manager.aexists():
            raise BusinessException("001")

        order = await order_manager.select_related("flow_instance").afirst()
        if not order or not order.flow_instance_id:
            raise BusinessException("002")
        if order.flow_instance.status != FlowStatusChoices.RUNNING:
            raise BusinessException("002")

        def _do_action():
            engine = FlowEngine(order.flow_instance)
            if data.action == "approve":
                current_node = order.flow_instance.current_node
                node_schema = View._hydrate_form_schema(
                    View._strip_form_schema_ui(getattr(current_node, "form_schema", None)),
                    current_node,
                )
                context_updates = build_context_updates_from_form_data(
                    form_schema=node_schema,
                    form_data=data.form_data or {},
                    existing_context=order.flow_instance.context or {},
                    node_code=getattr(current_node, "code", "") or "",
                )
                engine.approve(
                    user=request.user,
                    comment=data.operator_memo,
                    context=context_updates,
                    task_id=data.task_id,
                )
                return
            if data.action == "reject":
                engine.reject(
                    user=request.user,
                    comment=data.operator_memo,
                    task_id=data.task_id,
                )
                return
            raise BusinessException("004")

        try:
            await sync_to_async(_do_action, thread_sensitive=True)()
        except FlowEngineError:
            raise BusinessException("003")
