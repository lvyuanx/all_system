from django.urls import path
from .page_views.order_page import (
    order_add,
    order_shipping
)


urls = [
    path("order/order/add/", order_add, name="order_add"),
    path("order/order/shipping/", order_shipping, name="order_shipping"),
]
