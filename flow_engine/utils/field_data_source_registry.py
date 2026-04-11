# -*- coding:utf-8 -*-

from __future__ import annotations

from typing import Any, Protocol


class DefaultValueSourceProtocol(Protocol):
    def __call__(
        self,
        *,
        field: dict[str, Any],
        config: dict[str, Any],
        context: dict[str, Any],
        runtime_env: dict[str, Any] | None,
        options: list[dict[str, Any]],
    ) -> Any: ...


class FieldOptionsSourceProtocol(Protocol):
    def __call__(
        self,
        *,
        field: dict[str, Any],
        config: dict[str, Any],
        context: dict[str, Any],
        runtime_env: dict[str, Any] | None,
    ) -> list[dict[str, Any]]: ...


class FieldDataSourceRegistry:
    def __init__(self):
        self._sources: dict[str, Any] = {}

    @staticmethod
    def _normalize_key(source_type: str | None) -> str:
        return str(source_type or "").strip().lower()

    def register(self, source_type: str, resolver: Any):
        key = self._normalize_key(source_type)
        if not key:
            raise ValueError("source_type is required")
        if not callable(resolver):
            raise TypeError("resolver must be callable")
        self._sources[key] = resolver

    def unregister(self, source_type: str):
        self._sources.pop(self._normalize_key(source_type), None)

    def get(self, source_type: str | None):
        return self._sources.get(self._normalize_key(source_type))

    def resolve(self, source_type: str | None, default=None, **kwargs):
        resolver = self.get(source_type)
        if resolver is None:
            return default
        return resolver(**kwargs)

    def keys(self) -> list[str]:
        return sorted(self._sources.keys())
