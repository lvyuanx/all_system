from datetime import datetime
from decimal import Decimal
from django.contrib import admin
from pathlib import Path
from zoneinfo import ZoneInfo
from types import SimpleNamespace

from django.test import SimpleTestCase

import order.services
from order.admin import OrderAdmin
from order.enums import OrderStatusChoices
from core.exceptions.base_exceptions import BusinessException
from order.apis import apis as order_apis
from order.mobile_apis import apis as order_mobile_apis
from order.models import Order
from order.views.mobile_order_action_views import ConfirmView
from order.views import mobile_order_list_view
from order.views.dashboard.dashboard_trend_view import DashboardTrendView


class _TrendQuerySet:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []
        self.selected_fields = None

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        return self

    def order_by(self, *fields):
        return self

    def values_list(self, *fields):
        self.selected_fields = fields
        return self.rows

    def annotate(self, *args, **kwargs):
        raise AssertionError("trend aggregation should not use database date truncation")


class _ConfirmUserQuerySet:
    def __init__(self, rows):
        self.rows = rows
        self.value_fields = None
        self.expression_fields = None

    def values(self, *fields, **expressions):
        self.value_fields = fields
        self.expression_fields = expressions
        if "user_id" in expressions:
            raise ValueError("The annotation 'user_id' conflicts with a field on the model.")
        return self

    def order_by(self, *fields):
        return self

    def __iter__(self):
        return iter(self.rows)


class DashboardTrendViewTests(SimpleTestCase):
    def test_trend_aggregation_does_not_require_database_datetime_truncation(self):
        tz = ZoneInfo("Asia/Shanghai")
        start_dt = datetime(2026, 5, 11, tzinfo=tz)
        end_dt = datetime(2026, 5, 18, tzinfo=tz)
        rows = [
            (datetime(2026, 5, 11, 10, tzinfo=tz), Decimal("10000.00")),
            (datetime(2026, 5, 11, 18, tzinfo=tz), Decimal("25000.00")),
            (datetime(2026, 5, 14, 9, tzinfo=tz), Decimal("30000.00")),
        ]
        qs = _TrendQuerySet(rows)

        daily = DashboardTrendView._build_daily(qs, start_dt, end_dt)
        weekly = DashboardTrendView._build_weekly(qs, start_dt, end_dt)

        self.assertEqual(qs.selected_fields, ("create_time", "payable_amount"))
        self.assertEqual(
            daily["x"],
            ["05-11", "05-12", "05-13", "05-14", "05-15", "05-16", "05-17"],
        )
        self.assertEqual(daily["count"], [2, 0, 0, 1, 0, 0, 0])
        self.assertEqual(daily["amount"], [3.5, 0, 0, 3.0, 0, 0, 0])
        self.assertEqual(weekly, {"x": ["第1周"], "count": [3], "amount": [6.5]})


class ConfirmUserOptionsTests(SimpleTestCase):
    def test_confirm_user_queryset_filters_users_with_confirm_permission(self):
        class _StaffQuerySet:
            def __init__(self):
                self.select_related_args = None
                self.filter_kwargs = None
                self.distinct_called = False

            def select_related(self, *args):
                self.select_related_args = args
                return self

            def filter(self, **kwargs):
                self.filter_kwargs = kwargs
                return self

            def distinct(self):
                self.distinct_called = True
                return self

        class _StaffObjects:
            def __init__(self, qs):
                self.qs = qs

            def select_related(self, *args):
                return self.qs.select_related(*args)

        qs = _StaffQuerySet()
        original_objects = order.services.Staff.objects
        order.services.Staff.objects = _StaffObjects(qs)
        try:
            order.services.get_confirm_user_queryset(10)
        finally:
            order.services.Staff.objects = original_objects

        self.assertEqual(qs.select_related_args, ("user", "site"))
        self.assertEqual(qs.filter_kwargs["site_id"], 10)


class OrderConfirmPermissionTests(SimpleTestCase):
    class _User:
        def __init__(self, pk, has_confirm_perm=True, is_superuser=False):
            self.pk = pk
            self._has_confirm_perm = has_confirm_perm
            self.is_superuser = is_superuser

        def has_perm(self, perm):
            return self._has_confirm_perm

    def test_confirm_permission_allows_assigned_user_or_superuser_only(self):
        assigned_order = SimpleNamespace(order_status=OrderStatusChoices.CREATED, confirm_user_id=2)
        unassigned_order = SimpleNamespace(order_status=OrderStatusChoices.CREATED, confirm_user_id=None)
        other_order = SimpleNamespace(order_status=OrderStatusChoices.CONFIRMED, confirm_user_id=2)

        self.assertTrue(order.services.can_order_confirm(assigned_order, self._User(2)))
        self.assertFalse(order.services.can_order_confirm(unassigned_order, self._User(3)))
        self.assertTrue(order.services.can_order_confirm(assigned_order, self._User(9, has_confirm_perm=False, is_superuser=True)))
        self.assertFalse(order.services.can_order_confirm(assigned_order, self._User(3)))

    def test_admin_confirm_button_uses_shared_confirm_rule(self):
        admin_instance = OrderAdmin(Order, admin.site)
        assigned_order = SimpleNamespace(order_status=OrderStatusChoices.CREATED, confirm_user_id=2)
        unassigned_order = SimpleNamespace(order_status=OrderStatusChoices.CREATED, confirm_user_id=None)
        other_order = SimpleNamespace(order_status=OrderStatusChoices.CONFIRMED, confirm_user_id=2)

        self.assertTrue(admin_instance.can_confirm_order(assigned_order, SimpleNamespace(user=self._User(2))))
        self.assertFalse(admin_instance.can_confirm_order(unassigned_order, SimpleNamespace(user=self._User(3))))
        self.assertTrue(
            admin_instance.can_confirm_order(
                assigned_order,
                SimpleNamespace(user=self._User(9, has_confirm_perm=False, is_superuser=True)),
            )
        )
        self.assertFalse(admin_instance.can_confirm_order(assigned_order, SimpleNamespace(user=self._User(3))))
        self.assertFalse(admin_instance.can_confirm_order(other_order, SimpleNamespace(user=self._User(2))))

    def test_confirm_user_options_uses_model_user_id_field_without_annotation_conflict(self):
        rows = [
            {
                "user_id": 1,
                "staff_code": "S001",
                "full_name": "张三",
                "phone": "13800000000",
            }
        ]
        qs = _ConfirmUserQuerySet(rows)
        original_get_queryset = order.services.get_confirm_user_queryset
        order.services.get_confirm_user_queryset = lambda site_id: qs
        try:
            result = order.services.get_confirm_user_options(10)
        finally:
            order.services.get_confirm_user_queryset = original_get_queryset

        self.assertEqual(result, rows)
        self.assertIn("user_id", qs.value_fields)
        self.assertNotIn("user_id", qs.expression_fields)


class OrderAddTemplateTests(SimpleTestCase):
    def test_confirm_user_options_use_explicit_closing_tags(self):
        template = Path("order/templates/order/order_add.html").read_text(encoding="utf-8")

        self.assertIn('key="confirm-user-random"', template)
        self.assertIn("</el-option>", template)
        self.assertNotIn('<el-option label="系统随机分配" :value="null" />', template)

    def test_existing_order_submit_uses_confirm_endpoint(self):
        template = Path("order/templates/order/order_add.html").read_text(encoding="utf-8")

        self.assertIn('request.post("/order/confirm"', template)
        self.assertIn("const canSubmitOrder = computed", template)
        self.assertIn('request.post("/order/create"', template)

    def test_confirm_button_requires_order_confirm_permission(self):
        template = Path("order/templates/order/order_add.html").read_text(encoding="utf-8")

        self.assertIn("hasOrderConfirmPerm", template)
        self.assertIn('v-if="showSubmitButton"', template)
        self.assertIn("const showSubmitButton = computed", template)
        self.assertIn("return isEditMode && hasOrderConfirmPerm && pageData.fromData.order_status == 10", template)

    def test_create_page_loads_cached_order_create_habit(self):
        template = Path("order/templates/order/order_add.html").read_text(encoding="utf-8")

        self.assertIn('request.get("/order/create_habit"', template)
        self.assertIn("const loadCreateHabit = async () =>", template)
        self.assertIn("pageData.fromData.confirm_user_id = habit.confirm_user_id ?? null", template)


class OrderApiConfigTests(SimpleTestCase):
    def test_backend_confirm_endpoint_is_registered_for_admin_order_pages(self):
        endpoints = {item[1]: item[2] for item in order_apis[""]}

        self.assertIn("confirm", endpoints)

    def test_confirm_endpoint_requires_order_confirm_permission(self):
        self.assertEqual(ConfirmView.perms_all, Order.get_perms(["confirm"]))

    def test_create_habit_endpoints_are_registered_for_admin_and_mobile(self):
        backend_endpoints = {item[1]: item[2] for item in order_apis[""]}
        mobile_meta_endpoints = {item[1]: item[2] for item in order_mobile_apis["meta"]}

        self.assertIn("create_habit", backend_endpoints)
        self.assertIn("create_habit/", mobile_meta_endpoints)


class OrderCreateHabitTests(SimpleTestCase):
    def test_save_create_habit_writes_latest_payload_to_cache(self):
        cache_calls = {}

        def fake_set(key, value, timeout=None):
            cache_calls["set"] = (key, value, timeout)

        original_set = order.services.cache.set
        order.services.cache.set = fake_set
        try:
            order.services.save_order_create_habit(
                user_id=88,
                site_id=12,
                order_type=3,
                delivery_method=2,
                confirm_user_id=77,
            )
        finally:
            order.services.cache.set = original_set

        key, value, timeout = cache_calls["set"]
        self.assertEqual(key, "order:create_habit:88")
        self.assertEqual(
            value,
            {
                "site_id": 12,
                "order_type": 3,
                "delivery_method": 2,
                "confirm_user_id": 77,
            },
        )
        self.assertGreater(timeout, 0)

    def test_get_create_habit_returns_empty_payload_when_cache_missing(self):
        original_get = order.services.cache.get
        order.services.cache.get = lambda key, default=None: default
        try:
            result = order.services.get_order_create_habit(88)
        finally:
            order.services.cache.get = original_get

        self.assertEqual(
            result,
            {
                "site_id": None,
                "order_type": None,
                "delivery_method": None,
                "confirm_user_id": None,
            },
        )


class OrderAdminListDisplayTests(SimpleTestCase):
    def test_order_list_displays_order_creator_column(self):
        admin_instance = OrderAdmin(Order, admin.site)
        creator = SimpleNamespace(full_name="张三", username="creator")
        order_obj = SimpleNamespace(create_user=creator)

        self.assertIn("order_create_user", admin_instance.list_display)
        self.assertEqual(admin_instance.list_display[-2], "order_create_user")
        self.assertEqual(admin_instance.list_display[-1], "operate_buttons")
        self.assertEqual(admin_instance.order_create_user(order_obj), "张三")
        self.assertEqual(admin_instance.order_create_user.short_description, "订单创建人")


class MobileOrderListPermissionTests(SimpleTestCase):
    def test_mobile_order_list_detects_order_pool_filter_from_request_body(self):
        request = SimpleNamespace(
            body=b'{"filter":"{\\"order_status\\":[10]}"}',
        )

        self.assertTrue(mobile_order_list_view.is_order_pool_list_request(request))

    def test_mobile_order_list_uses_shared_order_pool_scope(self):
        source = Path("order/views/mobile_order_list_view.py").read_text(encoding="utf-8")

        self.assertIn("filter_order_pool_queryset(base_qs, cur_user)", source)
        self.assertIn("is_order_pool_list_request(request)", source)


class OrderCancelPermissionTests(SimpleTestCase):
    class _User:
        def __init__(self, pk, perms=None, is_superuser=False):
            self.pk = pk
            self._perms = set(perms or [])
            self.is_superuser = is_superuser

        def has_perm(self, perm):
            return perm in self._perms

    def test_cancel_memo_is_required_and_stripped(self):
        self.assertEqual(order.services.ensure_order_cancel_memo("  客户要求取消  "), "客户要求取消")

        with self.assertRaises(BusinessException) as cm:
            order.services.ensure_order_cancel_memo("  ")

        self.assertEqual(cm.exception.error_code, "007")

    def test_cancel_permission_allows_creator_only(self):
        creator = SimpleNamespace(pk=1)
        confirm_user = SimpleNamespace(pk=2)
        outsider = SimpleNamespace(pk=3)
        order_obj = SimpleNamespace(create_user_id=creator.pk, confirm_user_id=confirm_user.pk)

        order.services.ensure_order_cancel_user(order_obj, creator)

        with self.assertRaises(BusinessException) as cm:
            order.services.ensure_order_cancel_user(order_obj, confirm_user)

        self.assertEqual(cm.exception.error_code, "006")

        with self.assertRaises(BusinessException) as cm:
            order.services.ensure_order_cancel_user(order_obj, outsider)

        self.assertEqual(cm.exception.error_code, "006")

    def test_cancel_permission_rejects_user_without_id(self):
        order_obj = SimpleNamespace(create_user_id=None, confirm_user_id=None)

        with self.assertRaises(BusinessException):
            order.services.ensure_order_cancel_user(order_obj, SimpleNamespace(pk=None))

    def test_cancel_entrypoints_apply_creator_rule(self):
        admin_source = Path("order/admin.py").read_text(encoding="utf-8")
        mobile_action_source = Path("order/views/mobile_order_action_views.py").read_text(encoding="utf-8")
        status_action_source = Path("order/views/mobile_order_status_action_view.py").read_text(encoding="utf-8")

        self.assertIn("ensure_order_cancel_user(obj, request.user)", admin_source)
        self.assertIn("ensure_order_cancel_user(order, request.user)", mobile_action_source)
        self.assertIn('if data.action == "cancel":', status_action_source)
        self.assertIn("ensure_order_cancel_user(order, request.user)", status_action_source)

    def test_order_pool_visibility_allows_creator_or_confirm_user_and_superuser(self):
        order_obj = SimpleNamespace(create_user_id=1, confirm_user_id=2)

        self.assertTrue(order.services.can_order_pool_view(order_obj, SimpleNamespace(pk=1, is_superuser=False)))
        self.assertTrue(order.services.can_order_pool_view(order_obj, SimpleNamespace(pk=2, is_superuser=False)))
        self.assertTrue(order.services.can_order_pool_view(order_obj, SimpleNamespace(pk=9, is_superuser=True)))
        self.assertFalse(order.services.can_order_pool_view(order_obj, SimpleNamespace(pk=3, is_superuser=False)))

    def test_admin_add_button_requires_order_create_permission_in_order_pool(self):
        admin_instance = OrderAdmin(Order, admin.site)
        add_perm = Order.get_perms(["add"])[0]

        class _Get:
            def getlist(self, key):
                return [str(OrderStatusChoices.CREATED)] if key == "order_status" else []

        creator_request = SimpleNamespace(GET=_Get(), user=self._User(1, perms={add_perm}))
        confirm_request = SimpleNamespace(GET=_Get(), user=self._User(2, perms={Order.get_perms(["confirm"])[0]}))
        super_request = SimpleNamespace(GET=_Get(), user=self._User(9, is_superuser=True))

        self.assertTrue(admin_instance.has_add_permission(creator_request))
        self.assertFalse(admin_instance.has_add_permission(confirm_request))
        self.assertTrue(admin_instance.has_add_permission(super_request))

    def test_admin_operate_buttons_start_with_log_and_follow_identity_permissions(self):
        admin_instance = OrderAdmin(Order, admin.site)
        confirm_perm = Order.get_perms(["confirm"])[0]
        pay_perm = Order.get_perms(["pay"])[0]
        order_obj = SimpleNamespace(
            pk=10,
            order_status=OrderStatusChoices.CREATED,
            create_user_id=1,
            confirm_user_id=2,
        )

        confirm_request = SimpleNamespace(user=self._User(2, perms={confirm_perm}), get_full_path=lambda: "/admin/order/order/filter/?order_status=10")
        admin_instance._operate_buttons_request = confirm_request
        names = [item["name"] for item in admin_instance.get_operate_buttons_config(order_obj)]
        self.assertEqual(names[0], "操作日志")
        self.assertIn("确认", names)
        self.assertNotIn("取消", names)
        self.assertNotIn("支付", names)

        creator_request = SimpleNamespace(user=self._User(1), get_full_path=lambda: "/admin/order/order/filter/?order_status=10")
        admin_instance._operate_buttons_request = creator_request
        names = [item["name"] for item in admin_instance.get_operate_buttons_config(order_obj)]
        self.assertEqual(names[0], "操作日志")
        self.assertIn("取消", names)
        self.assertNotIn("确认", names)
        self.assertNotIn("支付", names)

        pay_request = SimpleNamespace(user=self._User(3, perms={pay_perm}), get_full_path=lambda: "/admin/order/order/filter/?order_status=10")
        admin_instance._operate_buttons_request = pay_request
        names = [item["name"] for item in admin_instance.get_operate_buttons_config(order_obj)]
        self.assertEqual(names[0], "操作日志")
        self.assertIn("支付", names)

    def test_payment_permission_helper_requires_pay_permission_or_superuser(self):
        pay_perm = Order.get_perms(["pay"])[0]

        self.assertTrue(order.services.can_order_pay(self._User(1, perms={pay_perm})))
        self.assertTrue(order.services.can_order_pay(self._User(9, is_superuser=True)))
        self.assertFalse(order.services.can_order_pay(self._User(2)))

    def test_admin_queryset_and_payment_api_use_shared_permission_helpers(self):
        admin_source = Path("order/admin.py").read_text(encoding="utf-8")
        pay_source = Path("order/views/pay/order_pay_view.py").read_text(encoding="utf-8")
        mobile_pay_source = Path("order/views/mobile_order_pay_view.py").read_text(encoding="utf-8")

        self.assertIn("filter_order_pool_queryset(qs, request.user)", admin_source)
        self.assertIn("can_order_pay(request.user)", pay_source)
        self.assertIn('("003", "暂无订单支付权限")', pay_source)
        self.assertIn("do_pay", mobile_pay_source)

    def test_admin_cancel_uses_row_button_and_dedicated_memo_view(self):
        admin_source = Path("order/admin.py").read_text(encoding="utf-8")

        self.assertNotIn('"batch_cancel"', admin_source)
        self.assertNotIn("def batch_cancel", admin_source)
        self.assertIn("def can_cancel_order(self, obj: Order, request: HttpRequest):", admin_source)
        self.assertIn('reverse("admin:order_order_cancel"', admin_source)
        self.assertIn('"name": "取消"', admin_source)
        self.assertIn('"type": "text"', admin_source)
        self.assertIn("def cancel_order_view(self, request: HttpRequest, object_id: str):", admin_source)
        self.assertIn('render(request, "order/admin/order_cancel.html"', admin_source)
        self.assertIn("memo = ensure_order_cancel_memo(request.POST.get(\"memo\"))", admin_source)
        self.assertIn("OrderStateMachine(obj, request.user, memo)", admin_source)

    def test_admin_confirm_uses_row_button_only(self):
        admin_source = Path("order/admin.py").read_text(encoding="utf-8")
        actions_block = admin_source.split("actions = [", 1)[1].split("def get_actions", 1)[0]

        self.assertIn('"name": "确认"', admin_source)
        self.assertIn("def can_confirm_order(self, obj: Order, request: HttpRequest):", admin_source)
        self.assertIn("return can_order_confirm(obj, request.user)", admin_source)
        self.assertIn('reverse("admin:order_order_confirm"', admin_source)
        self.assertIn("if request and self.can_confirm_order(obj, request):", admin_source)
        self.assertNotIn('"batch_confirm"', actions_block)
        self.assertNotIn('"batch_confirm"', admin_source.split("actions = [", 1)[1].split("def get_actions", 1)[0])

    def test_admin_operate_column_uses_fixed_right_styles(self):
        css_source = Path("order/static/order/css/order_admin.css").read_text(encoding="utf-8")
        mixin_source = Path("core/admin_extra/mixins/operate_buttons_mixin.py").read_text(encoding="utf-8")

        self.assertIn("#changelist-form .results", css_source)
        self.assertIn("overflow-x: auto", css_source)
        self.assertIn("position: sticky !important", css_source)
        self.assertIn("right: 0 !important", css_source)
        self.assertIn("width: 1%", css_source)
        self.assertIn(".admin-operate-buttons", css_source)
        self.assertIn("display: flex !important", css_source)
        self.assertIn('<span class="admin-operate-buttons">{}</span>', mixin_source)
        self.assertNotIn("display:inline-flex", mixin_source)


class OrderSiteIsolationTests(SimpleTestCase):
    def test_admin_queryset_is_filtered_by_current_user_site(self):
        source = Path("order/admin.py").read_text(encoding="utf-8")

        self.assertIn("def get_queryset(self, request):", source)
        self.assertIn("site_util.admin_filter_site(request, qs)", source)

    def test_order_page_entries_filter_by_current_user_site(self):
        source = Path("order/page_views/order_page.py").read_text(encoding="utf-8")

        self.assertIn("_get_order_or_404(request", source)
        self.assertNotIn("Order.objects.get(id=oid)", source)
        self.assertNotIn("Order.objects.get(pk=pk)", source)

    def test_superuser_is_not_site_filtered_by_shared_helper(self):
        from types import SimpleNamespace

        from site_mgmt.utils import site_util

        queryset = object()
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, is_superuser=True))

        self.assertIs(site_util.admin_filter_site(request, queryset), queryset)
