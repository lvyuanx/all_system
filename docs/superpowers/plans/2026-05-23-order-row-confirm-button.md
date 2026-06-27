# Order Row Confirm Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the order confirm entry into each row's operation column, and remove the top bulk-confirm action so only authorized users see a per-order confirm button.

**Architecture:** Reuse the existing `confirm_order_view` so the actual confirmation business rule stays in one place. The admin changelist will stop exposing `batch_confirm` in the top action bar, and `get_operate_buttons_config()` will append a row-level `确认` button only when the order is `CREATED`, the current user has the confirm permission, and the current user is the assigned confirm user for that order.

**Tech Stack:** Django admin, existing `OperateButtonsMixin`, existing `order/tests.py` regression tests.

---

### Task 1: Lock the behavior with regression tests

**Files:**
- Modify: `order/tests.py`

- [ ] **Step 1: Add assertions for row-level confirm visibility**

```python
def test_admin_confirm_button_moves_into_operate_column(self):
    admin_source = Path("order/admin.py").read_text(encoding="utf-8")

    self.assertIn('request.user.has_perm(Order.get_perms(["confirm"])[0])', admin_source)
    self.assertIn('"name": "确认"', admin_source)
    self.assertIn('reverse("admin:order_order_confirm"', admin_source)
    self.assertIn('if obj.order_status == OrderStatusChoices.CREATED', admin_source)
```

- [ ] **Step 2: Add assertions that the bulk action is no longer exposed**

```python
def test_admin_confirm_action_is_not_exposed_as_top_bulk_action(self):
    admin_source = Path("order/admin.py").read_text(encoding="utf-8")

    self.assertIn("actions = [", admin_source)
    self.assertIn('"batch_confirm"', admin_source)
    self.assertIn('actions.pop("batch_confirm", None)', admin_source)
```

- [ ] **Step 3: Run the focused test target and confirm the current code still fails the new expectations where needed**

Run: `.venv/bin/python manage.py test order.tests.OrderCancelPermissionTests`

Expected: existing tests pass, and the new assertions should fail until the implementation is added.

### Task 2: Move confirm into the per-row operate buttons

**Files:**
- Modify: `order/admin.py`

- [ ] **Step 1: Remove the bulk confirm action from the admin `actions` list**

```python
actions = [
    "batch_scheduled",
    "batch_producing",
    "batch_complete",
]
```

- [ ] **Step 2: Keep `get_actions()` pruning the remaining bulk actions by status**

```python
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
```

- [ ] **Step 3: Add a row-level confirm button inside `get_operate_buttons_config()`**

```python
        if (
            request
            and obj.order_status == OrderStatusChoices.CREATED
            and request.user.has_perm(Order.get_perms(["confirm"])[0])
        ):
            operate_buttons_config.insert(0, {
                "name": "确认",
                "type": "text",
                "mode": "link",
                "icon": "el-icon-check",
                "confirm": "确定确认该订单吗？",
                "url": lambda obj: reverse("admin:order_order_confirm", args=[obj.pk]),
            })
```

- [ ] **Step 4: Keep `confirm_order_view()` unchanged so the same permission and state checks still protect the action**

```python
def confirm_order_view(self, request: HttpRequest, object_id: str):
    obj = self.get_object(request, object_id)
    ...
    ensure_order_confirm_user(obj, request.user)
```

- [ ] **Step 5: Run a quick source check**

Run: `rg -n "batch_confirm|name\": \"确认\"|order_order_confirm" order/admin.py`

Expected: `batch_confirm` remains defined but is no longer in the top `actions` list; `确认` is present in `get_operate_buttons_config()`.

### Task 3: Verify the full order test suite

**Files:**
- None

- [ ] **Step 1: Run the order test suite**

Run: `.venv/bin/python manage.py test order.tests`

Expected: all tests pass.

- [ ] **Step 2: Inspect the final admin source if anything looks off**

Run: `sed -n '1,260p' order/admin.py`

Expected: confirm button only appears in the row operation config, and the top bulk confirm entry is gone.
