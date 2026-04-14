from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from core.utils.common_util import import_func_or_class
from flow_engine.data_sources.base import BaseFieldDataSource


class RuntimeFieldDataSourceRegistry:
    METADATA_FIELDS = (
        "key",
        "label",
        "data_type",
        "support_components",
        "supported_methods",
    )
    COMPONENT_VALUE_TYPES = {
        "input": "text",
        "textarea": "text",
        "number": "number",
        "title_h1": "text",
        "title_h2": "text",
        "title_h3": "text",
        "title_h4": "text",
        "title_h5": "text",
        "paragraph": "text",
        "select": "options",
        "radio": "options",
        "checkbox": "options",
        "switch": "boolean",
        "date": "date",
        "datetime": "datetime",
        "file": "file",
    }
    TARGETS = ("default", "options")
    VALID_DATA_TYPES = {
        "text",
        "number",
        "boolean",
        "radio",
        "checkbox",
        "date",
        "datetime",
        "select",
        "file",
    }
    VALID_SUPPORT_COMPONENTS = {
        "input",
        "textarea",
        "number",
        "title_h1",
        "title_h2",
        "title_h3",
        "title_h4",
        "title_h5",
        "paragraph",
        "select",
        "radio",
        "checkbox",
        "switch",
        "date",
        "datetime",
        "file",
    }

    def __init__(self):
        self._builtin_classes: dict[str, type[BaseFieldDataSource]] = {}

    @staticmethod
    def _normalize_key(key: str | None) -> str:
        return str(key or "").strip().lower()

    @classmethod
    def _normalize_components(cls, source_cls: type[BaseFieldDataSource]) -> list[str]:
        components: list[str] = []
        for item in (getattr(source_cls, "support_components", None) or []):
            component = str(item or "").strip().lower()
            if component:
                components.append(component)
        return components

    @classmethod
    def get_handler_method_name(cls, target: str, component: str) -> str:
        clean_target = str(target or "").strip().lower()
        clean_component = str(component or "").strip().lower()
        suffix = cls.COMPONENT_VALUE_TYPES.get(clean_component)
        if clean_target not in cls.TARGETS or not suffix:
            return ""
        return f"get_{clean_target}_{suffix}"

    @classmethod
    def _get_supported_methods(cls, source_cls: type[BaseFieldDataSource]) -> list[str]:
        methods: list[str] = []
        for suffix in sorted(set(cls.COMPONENT_VALUE_TYPES.values())):
            for target in cls.TARGETS:
                method_name = f"get_{target}_{suffix}"
                if callable(getattr(source_cls, method_name, None)):
                    methods.append(method_name)
        return methods

    @classmethod
    def _validate_source_cls(cls, source_cls: Any):
        if not isinstance(source_cls, type) or not issubclass(source_cls, BaseFieldDataSource):
            raise ValueError("field data source must inherit BaseFieldDataSource")

        key = cls._normalize_key(getattr(source_cls, "key", ""))
        if not key:
            raise ValueError("field data source key is required")

        label = str(getattr(source_cls, "label", "") or "").strip()
        if not label:
            raise ValueError(f"field data source '{key}' must define a non-empty label")

        data_type = str(getattr(source_cls, "data_type", "") or "").strip().lower()
        if data_type not in cls.VALID_DATA_TYPES:
            raise ValueError(f"field data source '{key}' has invalid data_type '{data_type}'")

        components = cls._normalize_components(source_cls)
        invalid_components = [item for item in components if item not in cls.VALID_SUPPORT_COMPONENTS]
        if invalid_components:
            invalid = ", ".join(sorted(set(invalid_components)))
            raise ValueError(f"field data source '{key}' has invalid support_components: {invalid}")

        supported_methods = cls._get_supported_methods(source_cls)
        if not supported_methods:
            raise ValueError(f"field data source '{key}' must implement at least one datasource method")

        if components:
            component_methods = {
                cls.get_handler_method_name(target, component)
                for component in components
                for target in cls.TARGETS
            }
            component_methods.discard("")
            if not component_methods.intersection(supported_methods):
                raise ValueError(
                    f"field data source '{key}' does not implement any datasource method for its support_components"
                )

        return key

    def register_builtin(self, source_cls: type[BaseFieldDataSource]):
        key = self._validate_source_cls(source_cls)
        if key in self._builtin_classes:
            raise ValueError(f"field data source key '{key}' is already registered")
        self._builtin_classes[key] = source_cls

    def _load_setting_classes(self) -> dict[str, type[BaseFieldDataSource]]:
        loaded: dict[str, type[BaseFieldDataSource]] = {}
        for item in getattr(settings, "FLOW_ENGINE_FIELD_DATA_SOURCES", []) or []:
            try:
                cls = import_func_or_class(item) if isinstance(item, str) else item
            except Exception as exc:
                raise ImproperlyConfigured(f"FLOW_ENGINE_FIELD_DATA_SOURCES contains an invalid import: {item}") from exc
            try:
                key = self._validate_source_cls(cls)
            except ValueError as exc:
                raise ImproperlyConfigured(str(exc)) from exc
            if key in self._builtin_classes or key in loaded:
                raise ImproperlyConfigured(f"field data source key '{key}' is duplicated")
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

    @classmethod
    def _build_metadata_item(cls, key: str, source_cls: type[BaseFieldDataSource]) -> dict[str, Any]:
        item = {
            "key": key,
            "label": str(getattr(source_cls, "label", "") or key),
            "data_type": str(getattr(source_cls, "data_type", "") or ""),
            "support_components": [
                str(component).strip()
                for component in (getattr(source_cls, "support_components", None) or [])
                if component is not None and str(component).strip()
            ],
            "supported_methods": list(cls._get_supported_methods(source_cls)),
        }
        return {field: item[field] for field in cls.METADATA_FIELDS}

    def metadata(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key, source_cls in sorted(self.all().items()):
            items.append(self._build_metadata_item(key, source_cls))
        return items

    def build(self, key: str | None, **kwargs):
        source_cls = self.get(key)
        if source_cls is None:
            return None
        return source_cls(**kwargs)
