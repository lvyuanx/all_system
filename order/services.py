import random

from django.db.models import Q
from django.db.models import F, QuerySet
from django.core.cache import cache

from core.exceptions.base_exceptions import BusinessException
from core.auth.models import User
from order.models import Order
from staff.models import Staff


ORDER_CREATE_HABIT_CACHE_TIMEOUT = 60 * 60 * 24 * 180


def _order_create_habit_cache_key(user_id: int | str) -> str:
    return f"order:create_habit:{user_id}"


def get_confirm_user_queryset(site_id: int) -> QuerySet:
    confirm_perm_codename = Order.get_pack_codenames(["confirm"])[0]
    return (
        Staff.objects.select_related("user", "site")
        .filter(
            site_id=site_id,
            user__is_active=True,
            user__groups__permissions__content_type__app_label=Order._meta.app_label,
            user__groups__permissions__codename=confirm_perm_codename,
        )
        .distinct()
    )


def get_confirm_user_options(site_id: int) -> list[dict]:
    return list(
        get_confirm_user_queryset(site_id)
        .values(
            "user_id",
            "staff_code",
            full_name=F("user__full_name"),
            phone=F("user__phone"),
        )
        .order_by("staff_code", "user_id")
    )


def choose_confirm_user(site_id: int, confirm_user_id: int | None) -> tuple[User, bool]:
    qs = get_confirm_user_queryset(site_id)
    if confirm_user_id:
        staff = qs.filter(user_id=confirm_user_id).first()
        if not staff:
            raise BusinessException("004")
        return staff.user, False

    user_ids = list(qs.values_list("user_id", flat=True))
    if not user_ids:
        raise BusinessException("005")
    selected_user_id = random.choice(user_ids)
    return User.objects.get(pk=selected_user_id), True


def _user_has_order_perm(user: User, perm_type: str) -> bool:
    if getattr(user, "is_superuser", False):
        return True
    perm = Order.get_perms([perm_type])[0]
    return bool(getattr(user, "has_perm", lambda perm: False)(perm))


def can_order_create(user: User) -> bool:
    return _user_has_order_perm(user, "add")


def can_order_pay(user: User) -> bool:
    return _user_has_order_perm(user, "pay")


def can_order_pool_view(order: Order, user: User) -> bool:
    if getattr(user, "is_superuser", False):
        return True
    user_id = getattr(user, "pk", None)
    return user_id is not None and user_id in {
        getattr(order, "create_user_id", None),
        getattr(order, "confirm_user_id", None),
    }


def filter_order_pool_queryset(qs: QuerySet, user: User) -> QuerySet:
    if getattr(user, "is_superuser", False):
        return qs
    user_id = getattr(user, "pk", None)
    if user_id is None:
        return qs.none()
    return qs.filter(Q(create_user_id=user_id) | Q(confirm_user_id=user_id))


def can_order_confirm(order: Order, user: User) -> bool:
    if getattr(user, "is_superuser", False):
        return True

    if not _user_has_order_perm(user, "confirm"):
        return False

    if not order.confirm_user_id:
        return False

    return order.confirm_user_id == user.pk


def ensure_order_confirm_user(order: Order, user: User):
    if can_order_confirm(order, user):
        return
    if not order.confirm_user_id:
        raise BusinessException("004")
    raise BusinessException("005")


def ensure_order_cancel_user(order: Order, user: User):
    if getattr(user, "is_superuser", False):
        return
    user_id = getattr(user, "pk", None)
    if user_id is None or user_id != order.create_user_id:
        raise BusinessException("006")


def ensure_order_cancel_memo(memo: str | None) -> str:
    memo = (memo or "").strip()
    if not memo:
        raise BusinessException("007")
    return memo


def save_order_create_habit(
    user_id: int | str,
    site_id: int,
    order_type: int,
    delivery_method: int,
    confirm_user_id: int | None,
):
    cache.set(
        _order_create_habit_cache_key(user_id),
        {
            "site_id": site_id,
            "order_type": order_type,
            "delivery_method": delivery_method,
            "confirm_user_id": confirm_user_id,
        },
        timeout=ORDER_CREATE_HABIT_CACHE_TIMEOUT,
    )


def get_order_create_habit(user_id: int | str) -> dict:
    habit = cache.get(_order_create_habit_cache_key(user_id), None)
    if not isinstance(habit, dict):
        habit = {}
    return {
        "site_id": habit.get("site_id"),
        "order_type": habit.get("order_type"),
        "delivery_method": habit.get("delivery_method"),
        "confirm_user_id": habit.get("confirm_user_id"),
    }
