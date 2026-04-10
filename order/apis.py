from .views import (
    order_delivery_all_list_view,
    order_type_all_list_view,
    order_create_view,
    order_info_view,
    order_ship_view,
    order_workflow_action_view,
    order_list_by_pattern_view,
)
from .views.dashboard import (
    DashboardSummaryView,
    DashboardTrendView,
    DashboardStatusView,
    DashboardSiteTopView,
    DashboardTypeView,
    DashboardDeliveryView,
    DashboardPendingShipView,
    DashboardPendingPayView,
)

from .views.pay import (
    order_pay_ca_list_view,
    order_pay_view,
    order_pay_method_type_all_list_view,
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
        (
            "A4",
            "ship",
            order_ship_view.View,
            "订单发货",
        ),
        (
            "A5",
            "list_by_pattern",
            order_list_by_pattern_view.View,
            "按版号查询关联订单",
        ),
        (
            "A6",
            "workflow_action",
            order_workflow_action_view.View,
            "订单流程操作",
        ),
    ],

    "dashboard": [
        ("D0", "dashboard_summary", DashboardSummaryView, "仪表盘汇总"),
        ("D1", "dashboard_trend", DashboardTrendView, "仪表盘趋势"),
        ("D2", "dashboard_status", DashboardStatusView, "仪表盘状态分布"),
        ("D3", "dashboard_site_top", DashboardSiteTopView, "仪表盘站点Top"),
        ("D4", "dashboard_type", DashboardTypeView, "仪表盘订单类型"),
        ("D5", "dashboard_delivery", DashboardDeliveryView, "仪表盘配送方式"),
        ("D6", "dashboard_pending_ship", DashboardPendingShipView, "待发货列表"),
        ("D7", "dashboard_pending_pay", DashboardPendingPayView, "待收款列表"),
    ],


    "pay": [
        (
            "B0",
            "ca_list",
            order_pay_ca_list_view.View,
            "查询订单支付流水",
        ),
        (
            "B1",
            "create",
            order_pay_view.View,
            "创建订单支付流水",
        ),
        (
            "B2",
            "pay_method_type_all_list",
            order_pay_method_type_all_list_view.View,
            "查询所有订单支付类型",
        ),
    ],
}

