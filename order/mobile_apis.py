from order.views import (
    mobile_order_list_view,
    mobile_order_info_view,
    mobile_order_create_view,
    mobile_order_timeline_view,
    mobile_order_ship_view,
    mobile_order_pay_view,
    mobile_order_list_by_pattern_view,
    order_confirm_user_options_view,
)
from order.views import mobile_order_meta_view
from order.views import mobile_order_action_views
from order.views import order_create_habit_view
from order.views import order_delivery_all_list_view, order_type_all_list_view
from order.views.pay import order_pay_ca_list_view, order_pay_method_type_all_list_view

apis = {
    "order": [
        ("A0", "list/", mobile_order_list_view.View, "移动端订单分页查询"),
        ("A1", "info/", mobile_order_info_view.View, "移动端订单详情"),
        ("A2", "create/", mobile_order_create_view.View, "移动端创建订单"),
        ("A3", "cancel/", mobile_order_action_views.CancelView, "移动端订单取消"),
        ("A4", "confirm/", mobile_order_action_views.ConfirmView, "移动端订单确认"),
        ("A5", "schedule/", mobile_order_action_views.ScheduleView, "移动端订单排产"),
        ("A6", "start_production/", mobile_order_action_views.StartProductionView, "移动端订单进入生产"),
        ("A7", "finish_production/", mobile_order_action_views.FinishProductionView, "移动端订单生产完成"),
        ("A8", "complete/", mobile_order_action_views.CompleteView, "移动端订单签收完成"),
        ("A9", "timeline/", mobile_order_timeline_view.View, "移动端订单日志"),
        ("A10", "ship/", mobile_order_ship_view.View, "移动端订单发货"),
        ("A11", "pay/", mobile_order_pay_view.View, "移动端订单支付"),
        ("A12", "list_by_pattern/", mobile_order_list_by_pattern_view.OrderModuleView, "移动端按版号查询订单"),
    ],
    "pay": [
        ("B0", "ca_list/", order_pay_ca_list_view.View, "移动端订单支付流水"),
        (
            "B1",
            "pay_method_type_all_list/",
            order_pay_method_type_all_list_view.View,
            "移动端支付方式列表",
        ),
    ],
    "meta": [
        ("C0", "order_type_all_list/", order_type_all_list_view.View, "移动端订单类型"),
        ("C1", "delivery_all_list/", order_delivery_all_list_view.View, "移动端配送方式"),
        ("C2", "receiver_options/", mobile_order_meta_view.MobileOrderReceiverOptionsView, "移动端收货方信息"),
        ("C3", "pay_status_all_list/", mobile_order_meta_view.MobileOrderPayStatusAllListView, "移动端订单支付状态"),
        ("C4", "ship_status_all_list/", mobile_order_meta_view.MobileOrderShipStatusAllListView, "移动端订单发货状态"),
        ("C5", "status_flow/", mobile_order_meta_view.MobileOrderStatusFlowView, "移动端订单状态流程"),
        ("C6", "confirm_user_options/", order_confirm_user_options_view.View, "移动端订单确认人选项"),
        ("C7", "create_habit/", order_create_habit_view.View, "移动端订单创建习惯"),
    ],
}
