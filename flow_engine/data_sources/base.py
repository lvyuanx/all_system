from __future__ import annotations

from typing import Any

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


class BaseFieldDataSource:
    key = ""
    label = ""
    data_type = ""
    support_components: list[str] = []

    def __init__(
        self,
        *,
        ctx: dict[str, Any] | None = None,
        request=None,
        field_schema: dict[str, Any] | None = None,
        instance=None,
        node_code: str = "",
        runtime_env: dict[str, Any] | None = None,
        source_config: dict[str, Any] | None = None,
        source_params: dict[str, Any] | None = None,
        component: str = "",
        target: str = "",
    ):
        self.ctx: dict[str, Any] = {}
        self.request = None
        self.field_schema: dict[str, Any] = {}
        self.instance = None
        self.node_code = ""
        self.runtime_env: dict[str, Any] = {}
        self.source_config: dict[str, Any] = {}
        self.source_params: dict[str, Any] = {}
        self.component = ""
        self.target = ""
        self.bind_runtime(
            ctx=ctx,
            request=request,
            field_schema=field_schema,
            instance=instance,
            node_code=node_code,
            runtime_env=runtime_env,
            source_config=source_config,
            source_params=source_params,
            component=component,
            target=target,
        )

    def bind_runtime(
        self,
        *,
        ctx: dict[str, Any] | None,
        request=None,
        field_schema: dict[str, Any] | None = None,
        instance=None,
        node_code: str = "",
        runtime_env: dict[str, Any] | None = None,
        source_config: dict[str, Any] | None = None,
        source_params: dict[str, Any] | None = None,
        component: str = "",
        target: str = "",
    ):
        self.ctx = ctx if isinstance(ctx, dict) else {}
        self.request = request
        self.field_schema = field_schema if isinstance(field_schema, dict) else {}
        self.instance = instance
        self.node_code = str(node_code or "")
        self.runtime_env = runtime_env if isinstance(runtime_env, dict) else {}
        self.source_config = source_config if isinstance(source_config, dict) else {}
        raw_source_params = source_params if isinstance(source_params, dict) else self.source_config.get("source_params")
        self.source_params = raw_source_params if isinstance(raw_source_params, dict) else {}
        self.component = str(component or "").strip().lower()
        self.target = str(target or "").strip().lower()
        return self

    def get_ctx_value(self, path: str, default: Any = _MISSING):
        return get_path(self.ctx, path, default)
