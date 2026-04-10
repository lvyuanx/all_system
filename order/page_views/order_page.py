import json

from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from core.utils import time_util
from order.models import Order, OrderCa, OrderStatusChoices, OrderPayStatusChoices, OrderPayMehtodChoices
from order.machine import OrderStateMachine
from flow_engine.models import FlowLog, FlowTask
from flow_engine.enums import FlowStatusChoices
from flow_engine.utils.form_runtime_util import resolve_form_runtime


def _get_prev_url(request):
    return request.META.get("HTTP_REFERER") or reverse("admin:order_order_changelist")


def _display_operator_name(name: str | None, default: str = "系统"):
    return name or default


def _display_operator_phone(phone: str | None):
    return phone or ""


def _strip_form_schema_ui(schema):
    if not isinstance(schema, dict):
        return schema
    cleaned = dict(schema)
    cleaned.pop("__ui", None)
    cleaned.pop("__form_library", None)
    return cleaned


def order_add(request):
    context = {
        "title": "订单创建",
    }
    return render(request, "order/order_add.html", {**context, "prev_url": _get_prev_url(request)})

def order_change(request, oid: int):
    order = Order.objects.get(id=oid)
    context = {
        "title": "订单编辑",
        "order_id": oid,            
        "is_disabled_mode": 0 if order.order_status in [OrderStatusChoices.CREATED] else 1,
    }
    return render(request, "order/order_add.html", {**context, "prev_url": _get_prev_url(request)})

def order_ship(request, pk: int):
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        raise Http404()
    
    context = {
        "title": "订单发货",
        "order_id": pk,
        "shipping_party": order.shipping_party,
        "shipping_party_company": order.shipping_party_company,
        "shipping_party_phone": order.shipping_party_phone,
        "shipping_party_address": order.shipping_party_address,
        "receiver_name": order.receiver_name,
        "receiver_company": order.receiver_company,
        "receiver_phone": order.receiver_phone,
        "receiver_address": order.receiver_address,
        "delivery_method": order.delivery_method,
        "pay_status": order.pay_status,
    }
    return render(request, "order/order_ship.html", context)


def order_pay(request, pk: int):
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        raise Http404()
    
    context = {
        "title": "订单发货",
        "order_id": pk,
        "pay_status_str": OrderPayStatusChoices(order.pay_status).label,
        "total_amount": order.total_amount,
        "discount_amount": order.discount_amount,
        "shipping_fee": order.shipping_fee,
        "payable_amount": order.payable_amount,
        "paid_amount": order.paid_amount,
    }
    return render(request, "order/order_pay.html", context)



def order_shipping(request):
    context = {
        "title": "发货单",
        "company_logo": "/media/system/company_default.png",
        "company_name": "上海某某有限公司",
        "order_no": "121213345235234",
        "create_time": "2025年1月1日",
        "shipping_party": "上海某某有限公司",
        "shipping_party_phone": "12345678901",
        "shipping_party_address": "上海某某大厦",
        "delivery_method": "送货上门",
        "receiver_name": "张三",
        "receiver_phone": "12345678901",
        "receiver_address": "上海某某大厦",
        "delivery_time": "2025年1月1日",
        "memo": "",
        "items": [
            {
                "item_name": "名称 - 1",
                "pattern_code": "A001",
                "color": "红色",
                "count": 11,
                "count_unit": "件",
                "memo": "",
            },
            {
                "item_name": "名称 - 2",
                "pattern_code": "A001",
                "color": "红色",
                "count": 11,
                "count_unit": "件",
                "memo": "",
            },
            {
                "item_name": "名称 - 3",
                "pattern_code": "A001",
                "color": "红色",
                "count": 11,
                "count_unit": "件",
                "memo": "",
            }
        ]
    }
    return render(request, "order/order_shipping.html", context)


order_status_title_dict = {
    OrderStatusChoices.CANCELED: "订单已取消，流程已终止",

    OrderStatusChoices.CREATED: "订单已创建，等待确认",
    OrderStatusChoices.CONFIRMED: "订单已确认，准备进入排产流程",

    OrderStatusChoices.SCHEDULED: "订单已排产，生产计划已生成",
    OrderStatusChoices.PRODUCING: "订单生产中，请耐心等待完工",

    OrderStatusChoices.FINISHED: "订单已完工，等待出库发货",

    OrderStatusChoices.SHIPPED: "订单已发货，等待客户签收",
    OrderStatusChoices.COMPLETED: "订单已完成，流程已结束",
}


def order_timeline(request, pk: int):
    manager = Order.objects.select_related(
        "flow_definition",
        "flow_instance",
        "flow_instance__current_node",
    ).filter(pk=pk)
    if not manager.exists():
        raise Http404()

    order = manager.first()
    if (
        order.order_status == OrderStatusChoices.PRODUCING
        and order.flow_instance_id
        and getattr(order.flow_instance, "status", None) == FlowStatusChoices.FINISHED
    ):
        sm = OrderStateMachine(
            order,
            request.user,
            "流程已完成，自动同步订单为已完工",
        )
        allowed, _ = sm.can_finish_production()
        if allowed:
            sm.finish_production()
            sm.save_state()
            order.refresh_from_db()
            order = (
                Order.objects.select_related(
                    "flow_definition",
                    "flow_instance",
                    "flow_instance__current_node",
                )
                .get(pk=pk)
            )
    obj = manager.values("create_user__full_name", "create_user__phone", "create_time").first()
    timeline_items = [{
        "item_title": "创建了一条订单",
        "item_user": _display_operator_name(obj["create_user__full_name"]),
        "item_phone": _display_operator_phone(obj["create_user__phone"]),
        "item_time": time_util.datetime_to_str(obj["create_time"]),
        "item_memo": "",
        "_sort_time": obj["create_time"],
    }]

    # 获取CA记录
    ca_manager = OrderCa.objects.filter(order__id=pk).order_by("id").values(
        "operator_name",
        "operator_phone",
        "operator_time",
        "operator_memo",
        "cur_status",
    )
    for ca in ca_manager:
        timeline_items.append({
            "item_user": _display_operator_name(ca["operator_name"]),
            "item_phone": _display_operator_phone(ca["operator_phone"]),
            "item_time": time_util.datetime_to_str(ca["operator_time"]),
            "item_memo": ca["operator_memo"],
            "item_title": order_status_title_dict.get(OrderStatusChoices(ca["cur_status"])),
            "_sort_time": ca["operator_time"],
        })

    if order and order.flow_definition_id and order.flow_instance_id:
        for log in FlowLog.objects.filter(instance_id=order.flow_instance_id).order_by("create_time"):
            title = log.message or f"流程动作: {log.action}"
            if log.action == "start":
                title = "流程已启动"
            elif log.action == "enter" and log.node_id:
                title = f"进入流程节点: {log.node.name}"
            elif log.action == "approve":
                title = "流程审批通过"
            elif log.action == "reject":
                title = "流程审批驳回"
            elif log.action == "reopen" and log.node_id:
                title = f"节点已退回，等待重新处理: {log.node.name}"
            elif log.action == "finish":
                title = "流程已完成，订单将自动完工"
            timeline_items.append({
                "item_user": _display_operator_name(getattr(log.user, "full_name", None)),
                "item_phone": _display_operator_phone(getattr(log.user, "phone", None)),
                "item_time": time_util.datetime_to_str(log.create_time),
                "item_memo": log.message if log.action not in {"start", "enter", "finish", "reopen"} else "",
                "item_title": title,
                "_sort_time": log.create_time,
            })

    timeline_lst = sorted(timeline_items, key=lambda item: item["_sort_time"])
    for item in timeline_lst:
        item.pop("_sort_time", None)

    context = {
        "title": "订单流水",
        "data_lst": timeline_lst,
        "order_id": pk,
    }
    return render(request, "order/order_timeline.html", context)


def _sync_order_workflow_state(order: Order, user):
    if (
        order.order_status == OrderStatusChoices.PRODUCING
        and order.flow_instance_id
        and getattr(order.flow_instance, "status", None) == FlowStatusChoices.FINISHED
    ):
        sm = OrderStateMachine(
            order,
            user,
            "流程已完成，自动同步订单为已完工",
        )
        allowed, _ = sm.can_finish_production()
        if allowed:
            sm.finish_production()
            sm.save_state()
            order.refresh_from_db()
            order = (
                Order.objects.select_related(
                    "flow_definition",
                    "flow_instance",
                    "flow_instance__current_node",
                    "flow_instance__flow_version",
                )
                .get(pk=order.pk)
            )
    return order


def _build_workflow_action_payload(request, order: Order):
    workflow_action = None
    if order.flow_instance_id and getattr(order.flow_instance, "status", None) == FlowStatusChoices.RUNNING:
        pending_qs = FlowTask.objects.filter(
            instance_id=order.flow_instance_id,
            status="pending",
        ).select_related("assignee", "node")
        if not request.user.is_superuser:
            pending_qs = pending_qs.filter(assignee=request.user)
        pending_tasks = list(pending_qs.order_by("id"))
        if pending_tasks:
            current_node = pending_tasks[0].node if pending_tasks[0].node_id else getattr(order.flow_instance, "current_node", None)
            raw_schema = _strip_form_schema_ui(getattr(current_node, "form_schema", None))
            runtime_schema, runtime_form_data = resolve_form_runtime(
                form_schema=raw_schema,
                context=order.flow_instance.context or {},
                node_code=getattr(current_node, "code", "") or "",
                runtime_env={
                    "business_type": order._meta.label,
                    "business_id": str(order.pk),
                    "order_id": order.pk,
                },
            )
            workflow_action = {
                "instance_id": order.flow_instance_id,
                "current_node_name": getattr(getattr(order.flow_instance, "current_node", None), "name", "") or "",
                "current_node_form_schema": runtime_schema,
                "current_form_data": runtime_form_data,
                "tasks": [
                    {
                        "task_id": task.id,
                        "group_key": task.group_key or "",
                        "assignee_name": getattr(task.assignee, "full_name", None) or getattr(task.assignee, "username", "") or "",
                        "node_name": getattr(task.node, "name", "") or "",
                    }
                    for task in pending_tasks
                ],
            }
    return workflow_action


def _build_workflow_node_steps(order: Order):
    if not order.flow_instance_id or not getattr(order.flow_instance, "flow_version_id", None):
        return []

    node_type_map = {
        "start": "开始",
        "task": "审批",
        "condition": "条件",
        "end": "结束",
    }
    state_label_map = {
        "done": "已完成",
        "current": "进行中",
        "upcoming": "未开始",
        "rejected": "已驳回",
    }

    nodes = list(order.flow_instance.flow_version.nodes.order_by("order", "id"))
    current_node_id = getattr(order.flow_instance, "current_node_id", None)
    flow_status = getattr(order.flow_instance, "status", None)
    current_seen = False
    step_items = []

    for node in nodes:
        state = "upcoming"
        if flow_status == FlowStatusChoices.FINISHED:
            state = "done"
        elif flow_status == FlowStatusChoices.REJECTED:
            if current_node_id and node.id == current_node_id:
                state = "rejected"
                current_seen = True
            elif not current_seen:
                state = "done"
        elif current_node_id:
            if node.id == current_node_id:
                state = "current"
                current_seen = True
            elif not current_seen:
                state = "done"

        step_items.append(
            {
                "node_name": node.name,
                "node_type_label": node_type_map.get(node.node_type, node.node_type),
                "state": state,
                "state_label": state_label_map.get(state, state),
                "is_auto": bool(getattr(node, "is_auto", False)),
            }
        )

    return step_items


def _build_workflow_recent_logs(order: Order):
    if not order.flow_instance_id:
        return []

    action_title_map = {
        "start": "流程启动",
        "enter": "进入节点",
        "approve": "审批通过",
        "reject": "审批驳回",
        "reopen": "退回当前节点重做",
        "finish": "流程完成",
    }
    tone_map = {
        "start": "brand",
        "enter": "brand",
        "approve": "success",
        "reject": "danger",
        "reopen": "danger",
        "finish": "success",
    }

    recent_logs = []
    log_qs = FlowLog.objects.filter(instance_id=order.flow_instance_id).select_related("user", "node").order_by("-create_time")[:12]
    for log in log_qs:
        title = action_title_map.get(log.action, log.action)
        if log.action == "enter" and log.node_id:
            title = f"进入 {log.node.name}"
        elif log.action == "finish":
            title = "流程已完成，订单自动完工"

        recent_logs.append(
            {
                "title": title,
                "time": time_util.datetime_to_str(log.create_time),
                "operator_name": _display_operator_name(
                    getattr(log.user, "full_name", None) or getattr(log.user, "username", None)
                ),
                "memo": log.message if log.action not in {"start", "enter", "finish", "reopen"} else "",
                "tone": tone_map.get(log.action, "muted"),
            }
        )
    return recent_logs


def _build_workflow_rework_note(order: Order):
    if not order.flow_instance_id or not getattr(order.flow_instance, "current_node_id", None):
        return None

    reject_log = (
        FlowLog.objects.filter(
            instance_id=order.flow_instance_id,
            node_id=order.flow_instance.current_node_id,
            action="reject",
        )
        .select_related("user")
        .order_by("-create_time")
        .first()
    )
    if not reject_log:
        return None

    has_pending = FlowTask.objects.filter(
        instance_id=order.flow_instance_id,
        node_id=order.flow_instance.current_node_id,
        status="pending",
    ).exists()
    if not has_pending:
        return None

    return {
        "time": time_util.datetime_to_str(reject_log.create_time),
        "operator_name": _display_operator_name(
            getattr(reject_log.user, "full_name", None) or getattr(reject_log.user, "username", None)
        ),
        "memo": reject_log.message or "",
    }


def order_workflow(request, pk: int):
    manager = Order.objects.select_related(
        "flow_definition",
        "flow_instance",
        "flow_instance__current_node",
        "flow_instance__flow_version",
    ).filter(pk=pk)
    if not manager.exists():
        raise Http404()

    order = _sync_order_workflow_state(manager.first(), request.user)
    workflow_action = _build_workflow_action_payload(request, order)
    workflow_steps = _build_workflow_node_steps(order)
    recent_logs = _build_workflow_recent_logs(order)
    rework_note = _build_workflow_rework_note(order)

    flow_status_label_map = {
        FlowStatusChoices.RUNNING: "进行中",
        FlowStatusChoices.FINISHED: "已完成",
        FlowStatusChoices.REJECTED: "已驳回",
        FlowStatusChoices.CANCELED: "已取消",
    }

    context = {
        "title": "订单流程工作台",
        "order_id": pk,
        "order_no": order.order_no,
        "order_status_label": OrderStatusChoices(order.order_status).label if getattr(order, "order_status", None) is not None else "",
        "receiver_name": order.receiver_name or "",
        "receiver_company": order.receiver_company or "",
        "flow_definition_name": getattr(order.flow_definition, "name", "") or "",
        "flow_status_label": flow_status_label_map.get(
            getattr(order.flow_instance, "status", None),
            getattr(order.flow_instance, "status", "") or "未启动",
        ),
        "current_node_name": getattr(getattr(order.flow_instance, "current_node", None), "name", "") or "",
        "create_time_str": time_util.datetime_to_str(getattr(order, "create_time", None)) if getattr(order, "create_time", None) else "",
        "workflow_action": workflow_action,
        "workflow_form_schema_json": json.dumps(
            (workflow_action or {}).get("current_node_form_schema") or {},
            ensure_ascii=False,
        ),
        "workflow_form_data_json": json.dumps(
            (workflow_action or {}).get("current_form_data") or {},
            ensure_ascii=False,
        ),
        "workflow_steps": workflow_steps,
        "recent_logs": recent_logs,
        "rework_note": rework_note,
        "active_task_count": len(workflow_action["tasks"]) if workflow_action else 0,
        "pending_task_total": FlowTask.objects.filter(
            instance_id=order.flow_instance_id,
            status="pending",
        ).count() if order.flow_instance_id else 0,
        "log_page_url": reverse("order_timeline", kwargs={"pk": pk}),
    }
    return render(request, "order/order_workflow.html", context)
