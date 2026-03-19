# -*-coding:utf-8 -*-
"""
订单数据看板接口聚合。每个具体接口位于 order/views/dashboard/ 下的独立文件。
保留该文件以兼容旧的导入路径。
"""
from .dashboard import (
    DashboardSummaryView,
    DashboardTrendView,
    DashboardStatusView,
    DashboardSiteTopView,
    DashboardTypeView,
    DashboardDeliveryView,
    DashboardPendingShipView,
    DashboardPendingPayView,
)

__all__ = [
    "DashboardSummaryView",
    "DashboardTrendView",
    "DashboardStatusView",
    "DashboardSiteTopView",
    "DashboardTypeView",
    "DashboardDeliveryView",
    "DashboardPendingShipView",
    "DashboardPendingPayView",
]
