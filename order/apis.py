from .views import (
    order_delivery_all_list_view,
    order_type_all_list_view,
    order_create_view,
    order_info_view,
)

apis = {
    "": [
        (
            "A0",
            "order_delivery_all_list",
            order_delivery_all_list_view.View,
            "查询所有配送方式",
        ),
        (
            "A1",
            "order_type_all_list",
            order_type_all_list_view.View,
            "查询所有订单类型",
        ),
        (
            "A2",
            "create",
            order_create_view.View,
            "创建订单",
        ),
        (
            "A3",
            "info",
            order_info_view.View,
            "查询订单详情",
        ),
    ]
}
