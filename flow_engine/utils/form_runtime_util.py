# -*- coding:utf-8 -*-

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from django.conf import settings

from core.utils.common_util import import_func_or_class
from flow_engine.utils.field_data_source_registry import FieldDataSourceRegistry

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

DEFAULT_VALUE_SOURCE_REGISTRY = FieldDataSourceRegistry()
FIELD_OPTIONS_SOURCE_REGISTRY = FieldDataSourceRegistry()


class BaseFieldDataSource:
    key = ""
    label = ""
    data_type = ""
    support_components: list[str] = []
    support_default = False
    support_options = False
    params_schema: list[dict[str, Any]] = []

    def __init__(
        self,
        *,
        ctx: dict[str, Any] | None,
        request=None,
        field_schema: dict[str, Any] | None = None,
        instance=None,
        node_code: str = "",
        runtime_env: dict[str, Any] | None = None,
    ):
        self.ctx = ctx if isinstance(ctx, dict) else {}
        self.request = request
        self.field_schema = field_schema if isinstance(field_schema, dict) else {}
        self.instance = instance
        self.node_code = str(node_code or "")
        self.runtime_env = runtime_env if isinstance(runtime_env, dict) else {}

    def get_config(self, target: str) -> dict[str, Any]:
        if target == "default":
            raw = self.field_schema.get("default_source_config")
        elif target == "options":
            raw = self.field_schema.get("options_source_config")
        else:
            raw = None
        return raw if isinstance(raw, dict) else {}

    def get_source_params(self, target: str) -> dict[str, Any]:
        raw = self.get_config(target).get("source_params")
        return raw if isinstance(raw, dict) else {}

    def get_ctx_value(self, path: str, default: Any = _MISSING):
        return get_path(self.ctx, path, default)

    def get_default(self, request):
        return _MISSING

    def get_options(self, request):
        return []


class RuntimeFieldDataSourceRegistry:
    def __init__(self):
        self._builtin_classes: dict[str, type[BaseFieldDataSource]] = {}

    @staticmethod
    def _normalize_key(key: str | None) -> str:
        return str(key or "").strip().lower()

    def register_builtin(self, source_cls: type[BaseFieldDataSource]):
        key = self._normalize_key(getattr(source_cls, "key", ""))
        if not key:
            raise ValueError("field data source key is required")
        self._builtin_classes[key] = source_cls

    def _load_setting_classes(self) -> dict[str, type[BaseFieldDataSource]]:
        loaded: dict[str, type[BaseFieldDataSource]] = {}
        for item in getattr(settings, "FLOW_ENGINE_FIELD_DATA_SOURCES", []) or []:
            try:
                cls = import_func_or_class(item) if isinstance(item, str) else item
            except Exception:
                continue
            if not isinstance(cls, type) or not issubclass(cls, BaseFieldDataSource):
                continue
            key = self._normalize_key(getattr(cls, "key", ""))
            if key:
                loaded[key] = cls
        return loaded

    def get(self, key: str | None):
        source_key = self._normalize_key(key)
        if not source_key:
            return None
        return self._load_setting_classes().get(source_key) or self._builtin_classes.get(source_key)

    def all(self) -> dict[str, type[BaseFieldDataSource]]:
        combined = dict(self._builtin_classes)
        combined.update(self._load_setting_classes())
        return combined

    def metadata(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key, source_cls in sorted(self.all().items()):
            support_components = [
                str(item).strip()
                for item in (getattr(source_cls, "support_components", None) or [])
                if item is not None and str(item).strip()
            ]
            params_schema = [
                deepcopy(item)
                for item in (getattr(source_cls, "params_schema", None) or [])
                if isinstance(item, dict)
            ]
            items.append(
                {
                    "key": key,
                    "label": str(getattr(source_cls, "label", "") or key),
                    "data_type": str(getattr(source_cls, "data_type", "") or ""),
                    "support_components": support_components,
                    "support_default": bool(getattr(source_cls, "support_default", False)),
                    "support_options": bool(getattr(source_cls, "support_options", False)),
                    "params_schema": params_schema,
                }
            )
        return items

    def build(self, key: str | None, **kwargs):
        source_cls = self.get(key)
        if source_cls is None:
            return None
        return source_cls(**kwargs)


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


class ContextTextDataSource(BaseFieldDataSource):
    key = "ctx_text"
    label = "流程上下文字段"
    data_type = "text"
    support_components = ["input", "textarea", "number", "date", "datetime"]
    support_default = True
    support_options = False

    def get_default(self, request):
        params = self.get_source_params("default")
        path = str(params.get("context_path") or "").strip()
        if not path:
            return _MISSING
        return self.get_ctx_value(path, _MISSING)


class OrderFieldTextDataSource(BaseFieldDataSource):
    key = "order_field_text"
    label = "订单字段文本"
    data_type = "text"
    support_components = ["input", "textarea", "number", "date", "datetime"]
    support_default = True
    support_options = False

    def get_default(self, request):
        params = self.get_source_params("default")
        field_name = params.get("field") or params.get("field_name")
        if not field_name:
            return _MISSING
        legacy_config = {
            "db_source_code": "order.field",
            "db_params": params,
            "field": field_name,
        }
        value = _resolve_db_value(legacy_config, self.ctx, self.runtime_env)
        if value in (None, ""):
            return _MISSING
        return value


class SiteAddressSelectDataSource(BaseFieldDataSource):
    key = "site_address_select"
    label = "站点地址选项"
    data_type = "select"
    support_components = ["select", "radio", "checkbox"]
    support_default = False
    support_options = True

    def get_options(self, request):
        params = self.get_source_params("options")
        legacy_config = {
            "db_source_code": "site.address_options_by_order",
            "db_params": params,
        }
        return _resolve_db_options(legacy_config, self.ctx, self.runtime_env)


RUNTIME_FIELD_DATA_SOURCE_REGISTRY = RuntimeFieldDataSourceRegistry()
RUNTIME_FIELD_DATA_SOURCE_REGISTRY.register_builtin(ContextTextDataSource)
RUNTIME_FIELD_DATA_SOURCE_REGISTRY.register_builtin(OrderFieldTextDataSource)
RUNTIME_FIELD_DATA_SOURCE_REGISTRY.register_builtin(SiteAddressSelectDataSource)


def get_registered_field_data_source_metadata() -> list[dict[str, Any]]:
    return RUNTIME_FIELD_DATA_SOURCE_REGISTRY.metadata()


def register_default_value_source(source_type: str, resolver):
    DEFAULT_VALUE_SOURCE_REGISTRY.register(source_type, resolver)


def unregister_default_value_source(source_type: str):
    DEFAULT_VALUE_SOURCE_REGISTRY.unregister(source_type)


def register_field_options_source(source_type: str, resolver):
    FIELD_OPTIONS_SOURCE_REGISTRY.register(source_type, resolver)


def unregister_field_options_source(source_type: str):
    FIELD_OPTIONS_SOURCE_REGISTRY.unregister(source_type)


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
    source_key = str(config.get("source_key") or "").strip()
    if not source_key:
        return None
    return RUNTIME_FIELD_DATA_SOURCE_REGISTRY.build(
        source_key,
        ctx=context,
        request=request,
        field_schema=field,
        instance=instance,
        node_code=node_code,
        runtime_env=runtime_env,
    )


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
        return _MISSING

    try:
        value = source.get_default(request)
    except Exception:
        value = _MISSING

    if value is not _MISSING and value not in (None, ""):
        return _json_safe(value)
    if "fallback_value" in cfg:
        return _json_safe(cfg.get("fallback_value"))
    return _MISSING


def _resolve_field_options_from_data_source(
    *,
    field: dict[str, Any],
    context: dict[str, Any],
    runtime_env: dict[str, Any] | None,
    request=None,
    instance=None,
    node_code: str = "",
    manual: list[dict[str, Any]],
):
    cfg = field.get("options_source_config") if isinstance(field.get("options_source_config"), dict) else {}
    mode = _source_config_mode(cfg)
    if not mode:
        return _MISSING

    if mode in {"fixed", "literal", "manual"}:
        return manual

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
        dynamic = source.get_options(request)
    except Exception:
        dynamic = []

    options = _normalize_options(dynamic or [])
    fallback_to_manual = bool(cfg.get("fallback_to_manual", True))
    if options:
        return options
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
    manual = FIELD_OPTIONS_SOURCE_REGISTRY.resolve(
        "manual",
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
        manual=manual,
    )
    if source_options is not _MISSING:
        return source_options

    cfg = field.get("options_config") if isinstance(field.get("options_config"), dict) else {}
    source_type = str(cfg.get("source_type") or "manual").strip().lower()

    if source_type in ("", "manual", "literal"):
        return manual

    dynamic = FIELD_OPTIONS_SOURCE_REGISTRY.resolve(
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
    resolved = DEFAULT_VALUE_SOURCE_REGISTRY.resolve(
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
