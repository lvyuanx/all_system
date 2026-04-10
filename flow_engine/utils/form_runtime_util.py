# -*- coding:utf-8 -*-

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from core.utils.common_util import import_func_or_class

ENUM_CLASS_PATH_MAP: dict[str, str] = {
    "order.type": "order.enums.OrderTypeChoices",
    "order.status": "order.enums.OrderStatusChoices",
    "order.pay_status": "order.enums.OrderPayStatusChoices",
    "order.pay_method": "order.enums.OrderPayMehtodChoices",
    "order.delivery_method": "order.enums.OrderDeliveryChoices",
    "order.ship_status": "order.enums.OrderShipStatusChoices",
    "flow.status": "flow_engine.enums.FlowStatusChoices",
    "flow.node_type": "flow_engine.enums.NodeTypeChoices",
}

_MISSING = object()


def get_path(data: Any, path: str, default: Any = _MISSING) -> Any:
    if not path:
        return default
    cur = data
    for part in str(path).split("."):
        if isinstance(cur, dict):
            if part not in cur:
                return default
            cur = cur.get(part)
            continue
        return default
    return cur


def set_path(data: dict[str, Any], path: str, value: Any):
    parts = [p for p in str(path).split(".") if p]
    if not parts:
        return
    cur = data
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def deep_merge_dict(base: dict[str, Any] | None, updates: dict[str, Any] | None) -> dict[str, Any]:
    left = deepcopy(base) if isinstance(base, dict) else {}
    right = updates if isinstance(updates, dict) else {}
    for key, value in right.items():
        if isinstance(value, dict) and isinstance(left.get(key), dict):
            left[key] = deep_merge_dict(left.get(key), value)
            continue
        left[key] = deepcopy(value)
    return left


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return value


def _field_list(form_schema: Any) -> list[dict[str, Any]]:
    if isinstance(form_schema, list):
        return [item for item in form_schema if isinstance(item, dict)]
    if isinstance(form_schema, dict):
        fields = form_schema.get("fields")
        if isinstance(fields, list):
            return [item for item in fields if isinstance(item, dict)]
    return []


def _normalize_options(raw: Any, label_key: str = "label", value_key: str = "value") -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    options: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            label = item.get(label_key)
            if label is None:
                label = item.get("label") if "label" in item else item.get("name")
            value = item.get(value_key)
            if value is None and value_key != "value":
                value = item.get("value")
            if value is None and "id" in item:
                value = item.get("id")
            if label is None:
                label = value
            options.append(
                {
                    "label": "" if label is None else str(label),
                    "value": _json_safe(value),
                    "default": bool(item.get("default", False)),
                }
            )
            continue
        options.append({"label": "" if item is None else str(item), "value": _json_safe(item), "default": False})
    return [opt for opt in options if opt.get("value") not in (None, "")]


def _resolve_enum_class(enum_code: str | None = None, enum_path: str | None = None):
    if enum_path:
        return import_func_or_class(enum_path)

    if not enum_code:
        return None
    candidate = str(enum_code).strip()
    if not candidate:
        return None

    if candidate.startswith("py:"):
        return import_func_or_class(candidate[3:])

    mapped = ENUM_CLASS_PATH_MAP.get(candidate)
    if mapped:
        return import_func_or_class(mapped)

    # 兼容直接传 Python 全路径
    if "." in candidate:
        try:
            return import_func_or_class(candidate)
        except Exception:
            return None

    return None


def resolve_enum_options(config: dict[str, Any] | None) -> list[dict[str, Any]]:
    cfg = config if isinstance(config, dict) else {}
    enum_cls = _resolve_enum_class(
        enum_code=cfg.get("enum_code"),
        enum_path=cfg.get("enum_path"),
    )
    if not enum_cls:
        return []

    options: list[dict[str, Any]] = []
    default_value = cfg.get("default_value")
    default_name = cfg.get("default_name")
    for item in enum_cls:
        is_default = False
        if default_name is not None and getattr(item, "name", None) == default_name:
            is_default = True
        if default_value is not None and getattr(item, "value", None) == default_value:
            is_default = True
        options.append(
            {
                "label": str(getattr(item, "label", getattr(item, "name", ""))),
                "value": _json_safe(getattr(item, "value", None)),
                "default": is_default,
                "name": getattr(item, "name", ""),
            }
        )
    return options


def _resolve_order_obj(context: dict[str, Any], runtime_env: dict[str, Any] | None, params: dict[str, Any] | None):
    runtime = runtime_env if isinstance(runtime_env, dict) else {}
    p = params if isinstance(params, dict) else {}

    order_id = p.get("order_id")
    if order_id in (None, ""):
        order_id_path = p.get("order_id_path") or "order_id"
        order_id = get_path(context, str(order_id_path), _MISSING)
        if order_id is _MISSING:
            order_id = runtime.get("order_id")
    if order_id in (None, ""):
        if runtime.get("business_type") == "order.Order":
            order_id = runtime.get("business_id")

    if order_id in (None, ""):
        return None

    from order.models import Order

    return (
        Order.objects.filter(pk=order_id)
        .values(
            "id",
            "order_no",
            "order_type",
            "order_status",
            "pay_status",
            "delivery_method",
            "receiver_name",
            "receiver_company",
            "receiver_phone",
            "receiver_address",
            "shipping_party",
            "shipping_party_company",
            "shipping_party_phone",
            "shipping_party_address",
            "site_id",
            "total_amount",
            "discount_amount",
            "shipping_fee",
            "payable_amount",
            "paid_amount",
        )
        .first()
    )


def _resolve_db_value(config: dict[str, Any], context: dict[str, Any], runtime_env: dict[str, Any] | None):
    code = str(config.get("db_source_code") or "").strip()
    params = config.get("db_params") if isinstance(config.get("db_params"), dict) else {}

    if code == "order.field":
        order_row = _resolve_order_obj(context, runtime_env, params)
        if not order_row:
            return None
        field_name = params.get("field") or config.get("field")
        if not field_name:
            return None
        return _json_safe(order_row.get(field_name))

    if code == "order.snapshot":
        order_row = _resolve_order_obj(context, runtime_env, params)
        return _json_safe(order_row) if order_row else None

    return None


def _resolve_db_options(config: dict[str, Any], context: dict[str, Any], runtime_env: dict[str, Any] | None):
    code = str(config.get("db_source_code") or "").strip()
    params = config.get("db_params") if isinstance(config.get("db_params"), dict) else {}

    if code == "site.address_options_by_order":
        order_row = _resolve_order_obj(context, runtime_env, params)
        site_id = order_row.get("site_id") if order_row else None
        if not site_id:
            return []

        from site_mgmt.models import SiteAddress

        rows = list(
            SiteAddress.objects.filter(site_id=site_id)
            .order_by("id")
            .values("id", "address_detail")[:200]
        )
        return _normalize_options(
            [
                {
                    "label": row.get("address_detail") or f"地址{row['id']}",
                    "value": row.get("id"),
                }
                for row in rows
            ]
        )

    return []


def _resolve_field_options(
    field: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    manual = _normalize_options(field.get("options") or field.get("choices") or field.get("enum") or [])
    cfg = field.get("options_config") if isinstance(field.get("options_config"), dict) else {}
    source_type = str(cfg.get("source_type") or "manual").strip().lower()

    if source_type in ("", "manual", "literal"):
        return manual

    label_key = str(cfg.get("label_key") or "label")
    value_key = str(cfg.get("value_key") or "value")
    dynamic: list[dict[str, Any]] = []

    if source_type == "enum":
        dynamic = _normalize_options(resolve_enum_options(cfg), label_key="label", value_key="value")
    elif source_type == "context":
        raw = get_path(context, str(cfg.get("context_path") or ""), _MISSING)
        if raw is not _MISSING:
            dynamic = _normalize_options(raw, label_key=label_key, value_key=value_key)
    elif source_type == "db":
        dynamic = _resolve_db_options(cfg, context, runtime_env)

    fallback_to_manual = bool(cfg.get("fallback_to_manual", True))
    if dynamic:
        return dynamic
    if fallback_to_manual:
        return manual
    return []


def _component_empty_default(field: dict[str, Any]) -> Any:
    component = str(field.get("component") or field.get("type") or "input").lower()
    if component == "switch":
        return False
    if component == "checkbox":
        return []
    if component == "file" and field.get("multiple"):
        return []
    return ""


def _resolve_default_from_config(
    field: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    options: list[dict[str, Any]],
):
    cfg = field.get("default_config") if isinstance(field.get("default_config"), dict) else {}
    source_type = str(cfg.get("source_type") or "literal").strip().lower()

    if source_type in ("", "literal"):
        if "value" in cfg:
            return _json_safe(cfg.get("value"))
        if "default" in field:
            return _json_safe(field.get("default"))
        return _json_safe(field.get("default_value"))

    if source_type == "context":
        path = str(cfg.get("context_path") or "")
        result = get_path(context, path, _MISSING)
        if result is not _MISSING:
            return _json_safe(result)

    if source_type == "enum":
        enum_options = resolve_enum_options(cfg)
        for item in enum_options:
            if item.get("default"):
                return _json_safe(item.get("value"))
        if options:
            return _json_safe(options[0].get("value"))

    if source_type == "db":
        value = _resolve_db_value(cfg, context, runtime_env)
        if value not in (None, ""):
            return _json_safe(value)

    if "fallback_value" in cfg:
        return _json_safe(cfg.get("fallback_value"))

    if "default" in field:
        return _json_safe(field.get("default"))
    return _json_safe(field.get("default_value"))


def _resolve_read_path(field: dict[str, Any], node_code: str) -> tuple[str, list[str]]:
    key = str(field.get("key") or field.get("name") or field.get("prop") or "").strip()
    binding = field.get("context_binding") if isinstance(field.get("context_binding"), dict) else None
    if not binding:
        return key, [key]

    default_path = f"form.{node_code}.{key}" if node_code else key
    read_path = str(binding.get("read_path") or default_path)
    fallback_paths = []
    if key and read_path != key:
        fallback_paths.append(key)
    return read_path, fallback_paths


def resolve_form_runtime(
    form_schema: Any,
    context: dict[str, Any] | None,
    node_code: str = "",
    runtime_env: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    runtime_context = context if isinstance(context, dict) else {}
    raw_fields = _field_list(form_schema)
    if not raw_fields:
        return deepcopy(form_schema), {}

    fields = deepcopy(raw_fields)
    form_data: dict[str, Any] = {}

    for field in fields:
        key = str(field.get("key") or field.get("name") or field.get("prop") or "").strip()
        if not key:
            continue

        resolved_options = _resolve_field_options(field, runtime_context, runtime_env)
        if resolved_options:
            field["options"] = resolved_options

        read_path, fallback_paths = _resolve_read_path(field, node_code)
        existing_value = get_path(runtime_context, read_path, _MISSING)
        if existing_value is _MISSING:
            for path in fallback_paths:
                existing_value = get_path(runtime_context, path, _MISSING)
                if existing_value is not _MISSING:
                    break

        if existing_value is not _MISSING:
            form_data[key] = _json_safe(existing_value)
            continue

        default_value = _resolve_default_from_config(field, runtime_context, runtime_env, resolved_options)
        if default_value not in (_MISSING, None):
            form_data[key] = _json_safe(default_value)
            continue

        form_data[key] = _component_empty_default(field)

    if isinstance(form_schema, dict):
        resolved_schema = deepcopy(form_schema)
        resolved_schema["fields"] = fields
        return resolved_schema, form_data

    return fields, form_data


def _resolve_write_binding(field: dict[str, Any], node_code: str, key: str) -> tuple[str, str]:
    binding = field.get("context_binding") if isinstance(field.get("context_binding"), dict) else None
    if not binding:
        return key, "overwrite"

    default_path = f"form.{node_code}.{key}" if node_code else key
    write_path = str(binding.get("write_path") or default_path)
    write_mode = str(binding.get("write_mode") or "overwrite").strip().lower()
    if write_mode not in {"overwrite", "merge_if_absent"}:
        write_mode = "overwrite"
    return write_path, write_mode


def build_context_updates_from_form_data(
    form_schema: Any,
    form_data: dict[str, Any] | None,
    existing_context: dict[str, Any] | None,
    node_code: str = "",
) -> dict[str, Any]:
    data = form_data if isinstance(form_data, dict) else {}
    existing = existing_context if isinstance(existing_context, dict) else {}
    fields = _field_list(form_schema)

    # 兜底兼容: 无字段定义时维持历史行为
    if not fields:
        return deepcopy(data)

    updates: dict[str, Any] = {}
    for field in fields:
        key = str(field.get("key") or field.get("name") or field.get("prop") or "").strip()
        if not key:
            continue
        if key not in data:
            continue

        write_path, write_mode = _resolve_write_binding(field, node_code, key)
        if write_mode == "merge_if_absent":
            existing_val = get_path(existing, write_path, _MISSING)
            if existing_val is not _MISSING and existing_val not in (None, ""):
                continue
        set_path(updates, write_path, _json_safe(data.get(key)))

    return updates
