from django.http import Http404
from django.shortcuts import render
from core.utils import time_util
from order.models import Order, OrderCa, OrderStatusChoices


def order_add(request):
    context = {
        "title": "订单创建",
    }
    return render(request, "order/order_add.html", context)

def order_change(request, oid: int):
    order = Order.objects.get(id=oid)
    context = {
        "title": "订单编辑",
        "order_id": oid,            
        "is_disabled_mode": 0 if order.order_status in [OrderStatusChoices.CREATED] else 1,
    }
    return render(request, "order/order_add.html", context)



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
    manager = Order.objects.filter(pk=pk)
    if not manager.exists():
        raise Http404()
    
    obj = manager.values("create_user__full_name", "create_user__phone", "create_time").first()
    timeline_lst = [{
        "item_title": "创建了一条订单",
        "item_user": obj["create_user__full_name"],
        "item_phone": obj["create_user__phone"],
        "item_time": time_util.datetime_to_str(obj["create_time"]),
        "item_memo": ""
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
        item = {
            "item_user": ca["operator_name"],
            "item_phone": ca["operator_phone"],
            "item_time": time_util.datetime_to_str(ca["operator_time"]),
            "item_memo": ca["operator_memo"],
            "item_title": order_status_title_dict.get(OrderStatusChoices(ca["cur_status"])),
        }
        timeline_lst.append(item)
    
    context = {
        "title": "订单流水",
        "data_lst": timeline_lst,
    }
    return render(request, "order/order_timeline.html", context)