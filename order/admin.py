from urllib.parse import urlencode

from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.http import url_has_allowed_host_and_scheme

from core.admin_extra.base_admin import AdminBaseMixin
from core.admin_extra.mixins.filter_change_list_mixin import FilterChangeListMixin
from core.admin_extra.mixins.operate_buttons_mixin import OperateButtonsMixin
from core.exceptions.base_exceptions import BusinessException
from core.utils import admin_util
from order.enums import OrderStatusChoices
from order.machine import OrderStateMachine
from order.models import Order
from order.services import (
    can_order_confirm,
    can_order_create,
    can_order_pay,
    ensure_order_cancel_memo,
    ensure_order_cancel_user,
    ensure_order_confirm_user,
    filter_order_pool_queryset,
)
from site_mgmt.utils import site_util
from .signals.signals import order_canceled_signal, order_complete_signal


@admin.register(Order)
class OrderAdmin(AdminBaseMixin, FilterChangeListMixin, OperateButtonsMixin, admin.ModelAdmin):
    class Media:
        css = {
            "all": ("order/css/order_admin.css",),
        }

    list_display = (
        "order_no",
        "order_type",
        "order_status",
        "confirm_user",
        "payable_amount",
        "receiver_name",
        "create_time",
        "pay_status",
        "ship_status",
        "order_create_user",
        "operate_buttons",
    )
    search_fields = ("receiver_name", "receiver_phone", "order_no")

    def order_create_user(self, obj: Order):
        user = obj.create_user
        if not user:
            return ""
        return getattr(user, "full_name", None) or getattr(user, "username", "")

    order_create_user.short_description = "订单创建人"

    # ------------------------------ 通用方法 ------------------------------
    def get_status_by_request(self, request: HttpRequest):
        status = request.GET.getlist("order_status")
        return [int(item) for item in status]

    def get_queryset(self, request):
        self._operate_buttons_request = request
        qs = super().get_queryset(request)
        qs = site_util.admin_filter_site(request, qs)
        status = self.get_status_by_request(request)
        if OrderStatusChoices.CREATED in status:
            qs = filter_order_pool_queryset(qs, request.user)
        return qs

    # ------------------------------ 基础按钮权限配置 ------------------------------
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        status = self.get_status_by_request(request)
        return OrderStatusChoices.CREATED in status and can_order_create(request.user)

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
        list_filter = ["receiver_name", "receiver_company", "create_time"]
        status = self.get_status_by_request(request)
        if not status or any(s >= OrderStatusChoices.FINISHED for s in status):
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

    def get_admin_next_url(self, request: HttpRequest):
        next_url = (
            request.POST.get("next")
            or request.GET.get("next")
            or request.META.get("HTTP_REFERER")
        )
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return next_url
        return reverse("admin:order_order_changelist")

    def can_cancel_order(self, obj: Order, request: HttpRequest):
        if obj.order_status not in [
            OrderStatusChoices.CREATED,
            OrderStatusChoices.CONFIRMED,
        ]:
            return False
        try:
            ensure_order_cancel_user(obj, request.user)
        except BusinessException:
            return False
        return True

    def can_confirm_order(self, obj: Order, request: HttpRequest):
        if obj.order_status != OrderStatusChoices.CREATED:
            return False
        return can_order_confirm(obj, request.user)

    def get_cancel_order_url(self, obj: Order, request: HttpRequest):
        url = reverse("admin:order_order_cancel", args=[obj.pk])
        return f"{url}?{urlencode({'next': request.get_full_path()})}"

    def get_operate_buttons_config(self, obj: Order):
        request = getattr(self, "_operate_buttons_request", None)
        operate_buttons_config = [
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
        if obj.order_status >= OrderStatusChoices.PRODUCING:
            operate_buttons_config.append({
                "name": "流程数据",
                "type": "text",
                "mode": "modal",
                "icon": "el-icon-data-analysis",
                "modal_width": "62vw",
                "modal_height": "82vh",
                "url": lambda obj: reverse("order_flow_context", kwargs={"pk": obj.pk}),
            })
        if obj.order_status == OrderStatusChoices.PRODUCING and not obj.flow_definition_id:
            operate_buttons_config.append({
                "name": "生产完成",
                "type": "text",
                "mode": "link",
                "icon": "el-icon-check",
                "confirm": "确定将该订单标记为生产完成吗？",
                "url": lambda obj: reverse("admin:order_order_finish_production", args=[obj.pk]),
            })
        if obj.order_status == OrderStatusChoices.PRODUCING and obj.flow_definition_id:
            operate_buttons_config.append({
                "name": "流程",
                "type": "text",
                "mode": "link",
                "icon": "el-icon-share",
                "url": lambda obj: reverse("order_workflow", kwargs={"pk": obj.pk}),
            })
        if obj.order_status == OrderStatusChoices.FINISHED:
            operate_buttons_config.append({
                "name": "发货",
                "type": "text",
                "mode": "modal",
                "icon": "el-icon-box",
                "modal_width": "50vw",
                "modal_height": "60vh",
                "url": lambda obj: reverse("order_ship", kwargs={"pk": obj.pk}),
            })
        if request and self.can_confirm_order(obj, request):
            operate_buttons_config.append({
                "name": "确认",
                "type": "text",
                "mode": "link",
                "icon": "el-icon-check",
                "confirm": "确定确认该订单吗？",
                "url": lambda obj: reverse("admin:order_order_confirm", args=[obj.pk]),
            })
        if request and self.can_cancel_order(obj, request):
            operate_buttons_config.append({
                "name": "取消",
                "type": "text",
                "mode": "link",
                "icon": "el-icon-close",
                "url": lambda obj: self.get_cancel_order_url(obj, request),
            })
        if request and can_order_pay(request.user):
            operate_buttons_config.append({
                "name": "支付",
                "type": "text",
                "mode": "modal",
                "icon": "el-icon-coin",
                "modal_width": "75vw",
                "modal_height": "80vh",
                "url": lambda obj: reverse("order_pay", kwargs={"pk": obj.pk}),
            })

        return operate_buttons_config

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/finish-production/",
                self.admin_site.admin_view(self.finish_production_view),
                name="order_order_finish_production",
            ),
            path(
                "<path:object_id>/cancel/",
                self.admin_site.admin_view(self.cancel_order_view),
                name="order_order_cancel",
            ),
            path(
                "<path:object_id>/confirm/",
                self.admin_site.admin_view(self.confirm_order_view),
                name="order_order_confirm",
            ),
        ]
        return custom_urls + urls

    def confirm_order_view(self, request: HttpRequest, object_id: str):
        obj = self.get_object(request, object_id)
        next_url = self.get_admin_next_url(request)
        if not obj:
            messages.error(request, "订单不存在")
            return redirect(reverse("admin:order_order_changelist"))

        if obj.order_status != OrderStatusChoices.CREATED:
            messages.warning(request, "只有已创建状态的订单才能确认")
            return redirect(next_url)

        try:
            ensure_order_confirm_user(obj, request.user)
        except BusinessException:
            messages.warning(request, "只有订单确认人可以确认订单")
            return redirect(next_url)

        with transaction.atomic():
            sm = OrderStateMachine(obj, request.user)
            sm.confirm()
            sm.save_state()
            admin_util.log_custom_actions(request, [obj], "订单确认", 2)
        messages.success(request, f"订单 {obj.order_no} 已确认")
        return redirect(next_url)

    def cancel_order_view(self, request: HttpRequest, object_id: str):
        obj = self.get_object(request, object_id)
        next_url = self.get_admin_next_url(request)
        if not obj:
            messages.error(request, "订单不存在")
            return redirect(reverse("admin:order_order_changelist"))

        if obj.order_status not in [
            OrderStatusChoices.CREATED,
            OrderStatusChoices.CONFIRMED,
        ]:
            messages.warning(request, "只有订单未排产前才能取消")
            return redirect(next_url)

        try:
            ensure_order_cancel_user(obj, request.user)
        except BusinessException:
            messages.warning(request, "只有订单创建人可以取消订单")
            return redirect(next_url)

        error_message = ""
        if request.method == "POST":
            try:
                memo = ensure_order_cancel_memo(request.POST.get("memo"))
            except BusinessException:
                error_message = "取消订单必须填写备注！"
            else:
                with transaction.atomic():
                    sm = OrderStateMachine(obj, request.user, memo)
                    sm.cancel()
                    sm.save_state()
                    admin_util.log_custom_actions(request, [obj], f"订单取消：{memo}", 2)
                    order_canceled_signal.send(sender=Order, instance=obj)
                messages.success(request, f"订单 {obj.order_no} 已取消")
                return redirect(next_url)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": obj,
            "title": "取消订单",
            "next_url": next_url,
            "error_message": error_message,
        }
        return render(request, "order/admin/order_cancel.html", context)

    def finish_production_view(self, request: HttpRequest, object_id: str):
        obj = self.get_object(request, object_id)
        if not obj:
            messages.error(request, "订单不存在")
            return redirect(reverse("admin:order_order_changelist"))

        if obj.order_status != OrderStatusChoices.PRODUCING:
            messages.warning(request, "只有生产中状态的订单才能生产完成")
        elif obj.flow_definition_id:
            messages.warning(request, "流程订单请在流程中完成审批后自动完工")
        else:
            sm = OrderStateMachine(obj, request.user)
            allowed, reason = sm.can_finish_production()
            if not allowed:
                messages.warning(request, reason or "当前订单暂不可生产完成")
            else:
                sm.finish_production()
                sm.save_state()
                admin_util.log_custom_actions(request, [obj], "订单生产完成", 2)
                messages.success(request, f"订单 {obj.order_no} 已生产完成")

        next_url = (
            request.GET.get("next")
            or request.META.get("HTTP_REFERER")
            or reverse("admin:order_order_changelist")
        )
        return redirect(next_url)

    # ------------------------------ 批量操作按钮配置 ------------------------------
    actions = [
        "batch_scheduled",
        "batch_producing",
        "batch_complete",
    ]

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("batch_finished", None)

        status = self.get_status_by_request(request)

        if OrderStatusChoices.CONFIRMED not in status:
            actions.pop("batch_scheduled", None)

        if OrderStatusChoices.SCHEDULED not in status:
            actions.pop("batch_producing", None)

        if OrderStatusChoices.SHIPPED not in status:
            actions.pop("batch_complete", None)

        return actions

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
        if queryset.filter(order_status=OrderStatusChoices.CREATED, confirm_user__isnull=True).exists():
            messages.warning(request, "存在未分配确认人的订单，请先分配确认人。")
            return
        if queryset.filter(order_status=OrderStatusChoices.CREATED).exclude(confirm_user=request.user).exists():
            messages.warning(request, "只有订单指定确认人可以确认订单，请检查勾选项！")
            return

        count = 0
        with transaction.atomic():
            for obj in queryset:
                if obj.order_status != OrderStatusChoices.CREATED:
                    continue
                ensure_order_confirm_user(obj, request.user)
                sm = OrderStateMachine(obj, request.user)
                sm.confirm()
                sm.save_state()
                count += 1
                admin_util.log_custom_actions(request, [obj], "订单确认", 2)
        messages.success(request, f"{count} 条记录已批量确认。")
        return redirect(request.get_full_path())

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
        skipped = 0
        with transaction.atomic():
            for obj in queryset:
                sm = OrderStateMachine(obj, request.user)
                allowed, _ = sm.can_finish_production()
                if not allowed:
                    skipped += 1
                    continue
                sm.finish_production()
                sm.save_state()
                count += 1
                admin_util.log_custom_actions(request, [obj], "订单生产完成", 2)
        if count:
            messages.success(request, f"{count} 条记录已批量生产完成。")
        if skipped:
            messages.warning(request, f"{skipped} 条订单已绑定流程且未完成，已跳过。")
    
    
    @admin_util.btn(
        short_description="批量签收",
        type="primary",
        confirm="确定批量签收选中的记录吗？",
    )
    def batch_complete(modeladmin, request, queryset):
        if not queryset.filter(
            order_status__in=[
                OrderStatusChoices.SHIPPED,
            ]
        ).exists():
            messages.warning(
                request,
                "只有[已发货]状态的订单才能签收,请检查勾选项！",
            )
            return

        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = OrderStateMachine(obj, request.user)
                sm.complete()
                sm.save_state()
                count += 1
                admin_util.log_custom_actions(request, [obj], "订单签收完成", 2)

                order_complete_signal.send(sender=Order, instance=obj)
        messages.success(request, f"{count} 条记录已批量签收完成。")
