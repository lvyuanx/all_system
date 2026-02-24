from django.contrib import admin, messages
from django.http import HttpRequest
from django.urls import reverse

from core.admin_extra.base_admin import AdminBaseMixin
from core.admin_extra.mixins.filter_change_list_mixin import FilterChangeListMixin
from core.admin_extra.mixins.operate_buttons_mixin import OperateButtonsMixin
from core.utils import admin_util
from order.enums import OrderStatusChoices
from order.machine import OrderStateMachine
from order.models import Order
from django.db import transaction


@admin.register(Order)
class OrderAdmin(
    AdminBaseMixin, FilterChangeListMixin, OperateButtonsMixin, admin.ModelAdmin
):

    list_display = (
        "order_no",
        "order_type",
        "order_status",
        "payable_amount",
        "receiver_name",
        "create_time",
        "pay_status",
        "ship_status",
        "operate_buttons",
    )
    search_fields = ("receiver_name", "receiver_phone", "order_no")

    # ------------------------------ 通用方法 ------------------------------
    def get_status_by_request(self, request: HttpRequest):
        status = request.GET.getlist("order_status")
        return [int(item) for item in status]

    # ------------------------------ 基础按钮权限配置 ------------------------------
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        status = self.get_status_by_request(request)
        if not status or OrderStatusChoices.CREATED in status:
            return True
        return False

    # ------------------------------ 字段超链接配置 ------------------------------
    list_display_links = ["order_no"]

    # def get_list_display_links(self, request, list_display):
    #     links = super().get_list_display_links(request, list_display) or []

    #     status = self.get_status_by_request(request)

    #     if OrderStatusChoices.CREATED not in status:
    #         if "order_no" in links:
    #             links.remove("order_no")

    #     return links

    # ------------------------------ 过滤器配置配置 ------------------------------
    # list_filter = ["receiver_name"]

    def get_list_filter(self, request):
        list_filter = ["receiver_name"]
        status = self.get_status_by_request(request)
        if any(s >= OrderStatusChoices.FINISHED for s in status):
            list_filter.extend(["pay_status", "ship_status"])
        return list_filter

    # ------------------------------ 行操作按钮 ------------------------------
    operate_buttons_config = [
        {
            "name": "发货",
            "type": "text",
            "mode": "modal",
            "icon": "el-icon-box",
            "modal_width": "50vw",
            "modal_height": "60vh",
            "url": lambda obj: reverse("order_ship", kwargs={"pk": obj.pk}),
        },
        {
            "name": "操作日志",
            "type": "text",
            "mode": "modal",
            "icon": "el-icon-date",
            "modal_width": "35vw",
            "modal_height": "80vh",
            "url": lambda obj: reverse("order_timeline", kwargs={"pk": obj.pk}),
        },
    ]

    def get_operate_buttons_config(self, obj: Order):
        operate_buttons_config = [
            {
                "name": "支付",
                "type": "text",
                "mode": "modal",
                "icon": "el-icon-coin",
                "modal_width": "75vw",
                "modal_height": "80vh",
                "url": lambda obj: reverse("order_pay", kwargs={"pk": obj.pk}),
            },
            {
                "name": "操作日志",
                "type": "text",
                "mode": "modal",
                "icon": "el-icon-date",
                "modal_width": "35vw",
                "modal_height": "80vh",
                "url": lambda obj: reverse("order_timeline", kwargs={"pk": obj.pk}),
            }
        ]
        if obj.order_status == OrderStatusChoices.FINISHED:
            operate_buttons_config = [
                {
                    "name": "发货",
                    "type": "text",
                    "mode": "modal",
                    "icon": "el-icon-box",
                    "modal_width": "50vw",
                    "modal_height": "60vh",
                    "url": lambda obj: reverse("order_ship", kwargs={"pk": obj.pk}),
                }
            ] + operate_buttons_config
        
        return operate_buttons_config

    # ------------------------------ 批量操作按钮配置 ------------------------------
    actions = [
        "batch_cancel",
        "batch_confirm",
        "batch_scheduled",
        "batch_producing",
        "batch_finished",
    ]

    def get_actions(self, request):
        actions = super().get_actions(request)

        status = self.get_status_by_request(request)

        if (
            OrderStatusChoices.CREATED not in status
            and OrderStatusChoices.CONFIRMED not in status
        ):
            del actions["batch_cancel"]

        if OrderStatusChoices.CREATED not in status:
            del actions["batch_confirm"]

        if OrderStatusChoices.CONFIRMED not in status:
            del actions["batch_scheduled"]

        if OrderStatusChoices.SCHEDULED not in status:
            del actions["batch_producing"]

        if OrderStatusChoices.PRODUCING not in status:
            del actions["batch_finished"]

        return actions

    @admin_util.btn(
        short_description="批量取消",
        icon="fa-solid fa-power-off",
        type="default",
        confirm="确定取消选中的记录吗？",
    )
    def batch_cancel(modeladmin, request, queryset):
        if not queryset.filter(
            order_status__in=[
                OrderStatusChoices.CREATED,
            ]
        ).exists():
            messages.warning(
                request,
                "只有订单未排产前才能批量取消,请检查勾选项！",
            )
            return

        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = OrderStateMachine(obj, request.user)
                sm.cancel()
                sm.save_state()
                count += 1
                admin_util.log_custom_actions(request, [obj], "订单取消", 2)
        messages.success(request, f"{count} 条记录已批量取消。")

    @admin_util.btn(
        short_description="批量确认",
        type="success",
        confirm="确定选中的记录吗？",
    )
    def batch_confirm(modeladmin, request, queryset):
        if not queryset.filter(
            order_status__in=[
                OrderStatusChoices.CREATED,
            ]
        ).exists():
            messages.warning(
                request,
                "只有[已创建]状态的订单才能确认订单,请检查勾选项！",
            )
            return

        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = OrderStateMachine(obj, request.user)
                sm.confirm()
                sm.save_state()
                count += 1
                admin_util.log_custom_actions(request, [obj], "订单确认", 2)
        messages.success(request, f"{count} 条记录已批量确认。")

    @admin_util.btn(
        short_description="批量排产",
        type="primary",
        confirm="确定批量排产选中的记录吗？",
    )
    def batch_scheduled(modeladmin, request, queryset):
        if not queryset.filter(
            order_status__in=[
                OrderStatusChoices.CONFIRMED,
            ]
        ).exists():
            messages.warning(
                request,
                "只有[已确认]状态的订单才能排产,请检查勾选项！",
            )
            return

        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = OrderStateMachine(obj, request.user)
                sm.schedule()
                sm.save_state()
                count += 1
                admin_util.log_custom_actions(request, [obj], "订单排产", 2)
        messages.success(request, f"{count} 条记录已批量排产。")

    @admin_util.btn(
        short_description="批量生产",
        type="primary",
        confirm="确定批量生产选中的记录吗？",
    )
    def batch_producing(modeladmin, request, queryset):
        if not queryset.filter(
            order_status__in=[
                OrderStatusChoices.SCHEDULED,
            ]
        ).exists():
            messages.warning(
                request,
                "只有[已排产]状态的订单才能进入生产,请检查勾选项！",
            )
            return

        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = OrderStateMachine(obj, request.user)
                sm.start_production()
                sm.save_state()
                count += 1
                admin_util.log_custom_actions(request, [obj], "订单生产", 2)
        messages.success(request, f"{count} 条记录已批量生产。")

    @admin_util.btn(
        short_description="批量生产完成",
        type="primary",
        confirm="确定批量生产完成选中的记录吗？",
    )
    def batch_finished(modeladmin, request, queryset):
        if not queryset.filter(
            order_status__in=[
                OrderStatusChoices.PRODUCING,
            ]
        ).exists():
            messages.warning(
                request,
                "只有[生产中]状态的订单才能进入完成生产,请检查勾选项！",
            )
            return

        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = OrderStateMachine(obj, request.user)
                sm.finish_production()
                sm.save_state()
                count += 1
                admin_util.log_custom_actions(request, [obj], "订单生产完成", 2)
        messages.success(request, f"{count} 条记录已批量生产完成。")
