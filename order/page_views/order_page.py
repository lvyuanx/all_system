from django.shortcuts import render


def order_add(request):
    context = {
        "title": "订单创建",
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