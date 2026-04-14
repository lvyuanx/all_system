# -*- coding:utf-8 -*-

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import logging
from typing import Any

from core.utils.common_util import import_func_or_class
from flow_engine.data_sources.base import _MISSING
from flow_engine.data_sources.registry import RuntimeFieldDataSourceRegistry
from flow_engine.utils.field_data_source_registry import FieldDataSourceRegistry

logger = logging.getLogger(__name__)

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

DEFAULT_VALUE_SOURCE_REGISTRY = FieldDataSourceRegistry()
FIELD_OPTIONS_SOURCE_REGISTRY = FieldDataSourceRegistry()


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


RUNTIME_FIELD_DATA_SOURCE_REGISTRY = RuntimeFieldDataSourceRegistry()


def get_registered_field_data_source_metadata() -> list[dict[str, Any]]:
    return RUNTIME_FIELD_DATA_SOURCE_REGISTRY.metadata()


def build_field_data_source_metadata_payload() -> dict[str, Any]:
    return {
        "items": get_registered_field_data_source_metadata(),
    }


def register_default_value_source(source_type: str, resolver):
    DEFAULT_VALUE_SOURCE_REGISTRY.register(source_type, resolver)


def unregister_default_value_source(source_type: str):
    DEFAULT_VALUE_SOURCE_REGISTRY.unregister(source_type)


def register_field_options_source(source_type: str, resolver):
    FIELD_OPTIONS_SOURCE_REGISTRY.register(source_type, resolver)


def unregister_field_options_source(source_type: str):
    FIELD_OPTIONS_SOURCE_REGISTRY.unregister(source_type)


def _safe_registry_resolve(registry: FieldDataSourceRegistry, source_type: str | None, default=None, **kwargs):
    try:
        return registry.resolve(source_type, default=default, **kwargs)
    except Exception:
        logger.exception("字段数据源旧版解析失败: source_type=%s", source_type)
        return default


def _default_value_source_literal(
    *,
    field: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    options: list[dict[str, Any]],
):
    if "value" in config:
        return _json_safe(config.get("value"))
    if "default" in field:
        return _json_safe(field.get("default"))
    return _json_safe(field.get("default_value"))


def _default_value_source_context(
    *,
    field: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    options: list[dict[str, Any]],
):
    result = get_path(context, str(config.get("context_path") or ""), _MISSING)
    if result is _MISSING:
        return _MISSING
    return _json_safe(result)


def _default_value_source_enum(
    *,
    field: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    options: list[dict[str, Any]],
):
    enum_options = resolve_enum_options(config)
    for item in enum_options:
        if item.get("default"):
            return _json_safe(item.get("value"))
    if options:
        return _json_safe(options[0].get("value"))
    return _MISSING


def _default_value_source_db(
    *,
    field: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    options: list[dict[str, Any]],
):
    value = _resolve_db_value(config, context, runtime_env)
    if value in (None, ""):
        return _MISSING
    return _json_safe(value)


def _field_options_source_manual(
    *,
    field: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    return _normalize_options(field.get("options") or field.get("choices") or field.get("enum") or [])


def _field_options_source_enum(
    *,
    field: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    return _normalize_options(resolve_enum_options(config), label_key="label", value_key="value")


def _field_options_source_context(
    *,
    field: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    raw = get_path(context, str(config.get("context_path") or ""), _MISSING)
    if raw is _MISSING:
        return []
    label_key = str(config.get("label_key") or "label")
    value_key = str(config.get("value_key") or "value")
    return _normalize_options(raw, label_key=label_key, value_key=value_key)


def _field_options_source_db(
    *,
    field: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    return _resolve_db_options(config, context, runtime_env)


register_default_value_source("literal", _default_value_source_literal)
register_default_value_source("context", _default_value_source_context)
register_default_value_source("enum", _default_value_source_enum)
register_default_value_source("db", _default_value_source_db)

register_field_options_source("manual", _field_options_source_manual)
register_field_options_source("literal", _field_options_source_manual)
register_field_options_source("enum", _field_options_source_enum)
register_field_options_source("context", _field_options_source_context)
register_field_options_source("db", _field_options_source_db)


def _source_config_mode(config: dict[str, Any]) -> str:
    mode = str(config.get("mode") or "").strip().lower()
    if mode:
        return mode
    if config.get("source_key"):
        return "data_source"
    if "value" in config:
        return "fixed"
    return ""


def _build_runtime_field_data_source(
    field: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    request=None,
    instance=None,
    node_code: str = "",
    target: str = "default",
):
    config_key = "default_source_config" if target == "default" else "options_source_config"
    config = field.get(config_key) if isinstance(field.get(config_key), dict) else {}
    component = str(field.get("component") or ("input" if target == "default" else "select")).strip().lower()
    source_params = config.get("source_params") if isinstance(config.get("source_params"), dict) else {}
    source_key = str(config.get("source_key") or "").strip()
    if not source_key:
        return None
    try:
        return RUNTIME_FIELD_DATA_SOURCE_REGISTRY.build(
            source_key,
            ctx=context,
            request=request,
            field_schema=field,
            instance=instance,
            node_code=node_code,
            runtime_env=runtime_env,
            source_config=config,
            source_params=source_params,
            component=component,
            target=target,
        )
    except Exception:
        logger.exception("构建字段数据源实例失败: source_key=%s", source_key)
        return None


def _call_runtime_field_data_source(source, *, target: str, component: str):
    method_name = RUNTIME_FIELD_DATA_SOURCE_REGISTRY.get_handler_method_name(target, component)
    if not method_name:
        return _MISSING
    handler = getattr(source, method_name, None)
    if not callable(handler):
        return _MISSING
    return handler()


def _resolve_default_from_data_source(
    field: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    request=None,
    instance=None,
    node_code: str = "",
):
    cfg = field.get("default_source_config") if isinstance(field.get("default_source_config"), dict) else {}
    mode = _source_config_mode(cfg)
    if not mode:
        return _MISSING

    if mode in {"fixed", "literal", "manual"}:
        if "value" in cfg:
            return _json_safe(cfg.get("value"))
        if "fallback_value" in cfg:
            return _json_safe(cfg.get("fallback_value"))
        return _MISSING

    if mode not in {"data_source", "datasource", "source"}:
        return _MISSING

    fallback_value = _MISSING
    if "fallback_value" in cfg:
        fallback_value = _json_safe(cfg.get("fallback_value"))

    source = _build_runtime_field_data_source(
        field=field,
        context=context,
        runtime_env=runtime_env,
        request=request,
        instance=instance,
        node_code=node_code,
        target="default",
    )
    if source is None:
        return fallback_value

    try:
        value = _call_runtime_field_data_source(
            source,
            target="default",
            component=str(field.get("component") or "input").strip().lower(),
        )
    except Exception:
        logger.exception("字段默认值数据源执行失败: source_key=%s", cfg.get("source_key"))
        return fallback_value

    if value is not _MISSING and value not in (None, ""):
        return _json_safe(value)
    return fallback_value


def _resolve_field_options_from_data_source(
    *,
    field: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    request=None,
    instance=None,
    node_code: str = "",
):
    cfg = field.get("options_source_config") if isinstance(field.get("options_source_config"), dict) else {}
    mode = _source_config_mode(cfg)
    if not mode:
        return _MISSING

    if mode in {"fixed", "literal", "manual"}:
        return []

    if mode not in {"data_source", "datasource", "source"}:
        return _MISSING

    source = _build_runtime_field_data_source(
        field=field,
        context=context,
        runtime_env=runtime_env,
        request=request,
        instance=instance,
        node_code=node_code,
        target="options",
    )
    if source is None:
        return _MISSING

    try:
        dynamic = _call_runtime_field_data_source(
            source,
            target="options",
            component=str(field.get("component") or "select").strip().lower(),
        )
    except Exception:
        logger.exception("字段选项数据源执行失败: source_key=%s", cfg.get("source_key"))
        dynamic = []

    if dynamic is _MISSING:
        return _MISSING
    options = _normalize_options(dynamic or [])
    if options:
        return options
    return _MISSING


def _resolve_field_options_from_legacy_config(
    *,
    field: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    manual: list[dict[str, Any]],
):
    raw_cfg = field.get("options_config")
    has_legacy_config = isinstance(raw_cfg, dict) and bool(raw_cfg)
    cfg = raw_cfg if isinstance(raw_cfg, dict) else {}
    source_type = str(cfg.get("source_type") or "manual").strip().lower()

    if source_type in ("", "manual", "literal"):
        return manual if has_legacy_config else _MISSING

    dynamic = _safe_registry_resolve(
        FIELD_OPTIONS_SOURCE_REGISTRY,
        source_type,
        default=[],
        field=field,
        config=cfg,
        context=context,
        runtime_env=runtime_env,
    ) or []

    fallback_to_manual = bool(cfg.get("fallback_to_manual", True))
    if dynamic:
        return dynamic
    if fallback_to_manual:
        return manual
    return []


def _resolve_field_options(
    field: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    request=None,
    instance=None,
    node_code: str = "",
) -> list[dict[str, Any]]:
    manual = _safe_registry_resolve(
        FIELD_OPTIONS_SOURCE_REGISTRY,
        "manual",
        default=[],
        field=field,
        config={},
        context=context,
        runtime_env=runtime_env,
    ) or []
    source_options = _resolve_field_options_from_data_source(
        field=field,
        context=context,
        runtime_env=runtime_env,
        request=request,
        instance=instance,
        node_code=node_code,
    )
    if source_options is not _MISSING:
        return source_options

    legacy_options = _resolve_field_options_from_legacy_config(
        field=field,
        context=context,
        runtime_env=runtime_env,
        manual=manual,
    )
    if legacy_options is not _MISSING:
        return legacy_options

    cfg = field.get("options_source_config") if isinstance(field.get("options_source_config"), dict) else {}
    mode = _source_config_mode(cfg)
    if mode in {"fixed", "literal", "manual"}:
        return manual
    if mode in {"data_source", "datasource", "source"}:
        return manual if bool(cfg.get("fallback_to_manual", True)) else []
    return manual


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
    request=None,
    instance=None,
    node_code: str = "",
):
    source_value = _resolve_default_from_data_source(
        field=field,
        context=context,
        runtime_env=runtime_env,
        request=request,
        instance=instance,
        node_code=node_code,
    )
    if source_value is not _MISSING:
        return source_value

    cfg = field.get("default_config") if isinstance(field.get("default_config"), dict) else {}
    source_type = str(cfg.get("source_type") or "literal").strip().lower()
    resolved = _safe_registry_resolve(
        DEFAULT_VALUE_SOURCE_REGISTRY,
        source_type,
        default=_MISSING,
        field=field,
        config=cfg,
        context=context,
        runtime_env=runtime_env,
        options=options,
    )
    if resolved is not _MISSING:
        return resolved

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


def _is_text_content_component(field: dict[str, Any]) -> bool:
    component = str(field.get("component") or field.get("type") or "").strip().lower()
    return component in {"title_h1", "title_h2", "title_h3", "title_h4", "title_h5", "paragraph"}


def resolve_form_runtime(
    form_schema: Any,
    context: dict[str, Any] | None,
    node_code: str = "",
    runtime_env: dict[str, Any] | None = None,
    request=None,
    instance=None,
) -> tuple[Any, dict[str, Any]]:
    runtime_context = context if isinstance(context, dict) else {}
    raw_fields = _field_list(form_schema)
    if not raw_fields:
        return deepcopy(form_schema), {}

    fields = deepcopy(raw_fields)
    form_data: dict[str, Any] = {}

    for field in fields:
        if _is_text_content_component(field):
            text_field = deepcopy(field)
            if "default" not in text_field:
                text_field["default"] = field.get("content", "")
            resolved_content = _resolve_default_from_config(
                text_field,
                runtime_context,
                runtime_env,
                [],
                request=request,
                instance=instance,
                node_code=node_code,
            )
            if resolved_content is not _MISSING and resolved_content is not None:
                field["content"] = _json_safe(resolved_content)
            continue

        key = str(field.get("key") or field.get("name") or field.get("prop") or "").strip()
        if not key:
            continue

        resolved_options = _resolve_field_options(
            field,
            runtime_context,
            runtime_env,
            request=request,
            instance=instance,
            node_code=node_code,
        )
        has_option_binding = any(
            key_name in field for key_name in ("options", "choices", "enum", "options_config", "options_source_config")
        )
        if resolved_options or has_option_binding:
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

        default_value = _resolve_default_from_config(
            field,
            runtime_context,
            runtime_env,
            resolved_options,
            request=request,
            instance=instance,
            node_code=node_code,
        )
        if default_value not in (_MISSING, None):
            form_data[key] = _json_safe(default_value)
            continue

        form_data[key] = _component_empty_default(field)

    if isinstance(form_schema, dict):
        resolved_schema = deepcopy(form_schema)
        resolved_schema["fields"] = fields
        return resolved_schema, form_data

    return fields, form_data


def _resolve_write_binding(field: dict[str, Any], node_code: str, key: str) -> tuple[list[str], str]:
    binding = field.get("context_binding") if isinstance(field.get("context_binding"), dict) else None
    if not binding:
        return [key], "overwrite"

    default_path = f"form.{node_code}.{key}" if node_code else key
    write_target = str(binding.get("write_target") or "").strip().lower()
    if write_target == "none":
        write_paths: list[str] = []
    elif write_target == "flow":
        write_paths = [key]
    elif write_target == "both":
        write_paths = [key]
        if default_path != key:
            write_paths.append(default_path)
    elif write_target == "node":
        write_paths = [default_path]
    else:
        write_path = str(binding.get("write_path") or default_path)
        write_paths = [write_path] if write_path else []
    write_mode = str(binding.get("write_mode") or "overwrite").strip().lower()
    if write_mode not in {"overwrite", "merge_if_absent"}:
        write_mode = "overwrite"
    return write_paths, write_mode


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

        write_paths, write_mode = _resolve_write_binding(field, node_code, key)
        if not write_paths:
            continue
        for write_path in write_paths:
            if write_mode == "merge_if_absent":
                existing_val = get_path(existing, write_path, _MISSING)
                if existing_val is not _MISSING and existing_val not in (None, ""):
                    continue
            set_path(updates, write_path, _json_safe(data.get(key)))

    return updates
