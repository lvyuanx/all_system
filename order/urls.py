from django.urls import path
from .page_views.order_page import (
    order_add,
    order_change,
    order_shipping,
    order_timeline
)


urls = [
    path("order/order/add/", order_add, name="order_add"),
    path("order/order/<int:oid>/change/", order_change, name="order_chnage"),
    path("order/order/shipping/", order_shipping, name="order_shipping"),
    path("order/order/<int:pk>/timeline/", order_timeline, name="order_timeline"),
]
