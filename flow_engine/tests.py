import json
import re
from types import SimpleNamespace
from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import get_template
from django.test import RequestFactory, SimpleTestCase, override_settings

from flow_engine.data_sources.base import BaseFieldDataSource as NewBaseFieldDataSource
from flow_engine.data_sources.registry import RuntimeFieldDataSourceRegistry as NewRuntimeFieldDataSourceRegistry
from flow_engine.page_views.flow_page import (
    field_data_source_metadata,
    flow_definition_add,
    flow_form_designer,
)
from flow_engine.views.field_data_source_metadata_view import View as FieldDataSourceMetadataApiView
from flow_engine.utils.form_designer_data_source_examples import (
    get_builtin_form_data_source_examples,
)
from flow_engine.data_sources import BaseFieldDataSource, RuntimeFieldDataSourceRegistry
from flow_engine.utils.form_runtime_util import (
    build_context_updates_from_form_data,
    get_registered_field_data_source_metadata,
    register_default_value_source,
    register_field_options_source,
    resolve_form_runtime,
    unregister_default_value_source,
    unregister_field_options_source,
)


class RuntimeEchoDataSource(BaseFieldDataSource):
    key = "runtime-echo"
    label = "Runtime Echo"
    data_type = "text"
    support_components = ["input", "textarea", "select"]

    def get_default_text(self):
        request_token = getattr(self.request, "trace_token", "missing-request")
        instance_id = getattr(self.instance, "id", "missing-instance")
        return (
            f"{self.source_params.get('prefix', 'pfx')}-"
            f"{self.node_code}-"
            f"{self.ctx.get('tenant', '')}-"
            f"{request_token}-"
            f"{instance_id}-"
            f"{self.runtime_env.get('business_id', '')}"
        )

    def get_options_options(self):
        return [
            {"label": f"{self.node_code}-{self.source_params.get('suffix', 'A')}", "value": self.ctx.get("tenant", "")},
            {
                "label": getattr(self.request, "trace_token", "missing-request"),
                "value": getattr(self.instance, "id", ""),
            },
        ]


class BlankDefaultDataSource(BaseFieldDataSource):
    key = "blank-default"
    label = "Blank Default"
    data_type = "text"
    support_components = ["input"]

    def get_default_text(self):
        return ""


class BlankOptionsDataSource(BaseFieldDataSource):
    key = "blank-options"
    label = "Blank Options"
    data_type = "select"
    support_components = ["select"]

    def get_options_options(self):
        return []


class ExplodingDefaultDataSource(BaseFieldDataSource):
    key = "exploding-default"
    label = "Exploding Default"
    data_type = "text"
    support_components = ["input"]

    def get_default_text(self):
        raise RuntimeError("default datasource failed")


class ExplodingOptionsDataSource(BaseFieldDataSource):
    key = "exploding-options"
    label = "Exploding Options"
    data_type = "select"
    support_components = ["select"]

    def get_options_options(self):
        raise RuntimeError("options datasource failed")


class SchemaAwareDefaultDataSource(BaseFieldDataSource):
    key = "schema-aware-default"
    label = "Schema Aware Default"
    data_type = "text"
    support_components = ["input"]

    def get_default_text(self):
        return (
            f"{self.field_schema.get('key')}|"
            f"{self.source_params.get('token')}|"
            f"{self.node_code}|"
            f"{self.ctx.get('tenant')}|"
            f"{self.runtime_env.get('business_id')}"
        )


class InjectedRequestDataSource(BaseFieldDataSource):
    key = "injected-request-default"
    label = "Injected Request Default"
    data_type = "text"
    support_components = ["input"]

    def get_default_text(self):
        return (
            f"{getattr(self.request, 'trace_token', 'missing-request')}|"
            f"{self.field_schema.get('key')}|"
            f"{getattr(self.instance, 'id', 'missing-instance')}|"
            f"{self.node_code}|"
            f"{self.ctx.get('tenant', '')}"
        )


class InjectedInstanceDataSource(BaseFieldDataSource):
    key = "injected-instance-default"
    label = "Injected Instance Default"
    data_type = "text"
    support_components = ["input"]

    def get_default_text(self):
        return (
            f"{getattr(self.instance, 'id', 'missing-instance')}|"
            f"{getattr(self.instance, 'business_id', 'missing-business-id')}|"
            f"{self.node_code}|"
            f"{self.field_schema.get('key')}|"
            f"{self.ctx.get('tenant', '')}"
        )


class InjectedOptionsDataSource(BaseFieldDataSource):
    key = "injected-options"
    label = "Injected Options"
    data_type = "select"
    support_components = ["select"]

    def get_options_options(self):
        return [
            {
                "label": (
                    f"{self.ctx.get('tenant', '')}|"
                    f"{getattr(self.request, 'trace_token', 'missing-request')}|"
                    f"{self.field_schema.get('key')}|"
                    f"{getattr(self.instance, 'id', 'missing-instance')}|"
                    f"{self.node_code}|"
                    f"{self.runtime_env.get('business_id', '')}|"
                    f"{self.source_params.get('token', '')}"
                ),
                "value": "runtime-option",
            }
        ]


class TextContentDataSource(BaseFieldDataSource):
    key = "text-content"
    label = "Text Content"
    data_type = "text"
    support_components = ["paragraph", "title_h1"]

    def get_default_text(self):
        return f"{self.source_params.get('prefix', 'text')}|{self.ctx.get('tenant', '')}|{self.node_code}"


class FormRuntimeDataSourceRegistryTests(SimpleTestCase):
    def test_legacy_default_config_and_manual_options_still_work(self):
        schema = {
            "fields": [
                {
                    "key": "status",
                    "component": "select",
                    "options": [
                        {"label": "draft", "value": "draft"},
                        {"label": "published", "value": "published"},
                    ],
                    "options_config": {"source_type": "manual"},
                    "default_config": {
                        "source_type": "context",
                        "context_path": "defaults.status",
                    },
                }
            ]
        }

        resolved_schema, resolved_form_data = resolve_form_runtime(
            form_schema=schema,
            context={"defaults": {"status": "published"}},
            node_code="NODE_A",
        )

        self.assertEqual(resolved_form_data["status"], "published")
        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [
                {"label": "draft", "value": "draft", "default": False},
                {"label": "published", "value": "published", "default": False},
            ],
        )

    def test_legacy_options_config_falls_back_to_manual_options(self):
        schema = {
            "fields": [
                {
                    "key": "address",
                    "component": "select",
                    "options": [
                        {"label": "default-address", "value": 1},
                    ],
                    "options_config": {
                        "source_type": "context",
                        "context_path": "missing.addresses",
                        "fallback_to_manual": True,
                    },
                }
            ]
        }

        resolved_schema, resolved_form_data = resolve_form_runtime(
            form_schema=schema,
            context={},
            node_code="NODE_A",
        )

        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [{"label": "default-address", "value": 1, "default": False}],
        )
        self.assertEqual(resolved_form_data["address"], "")

    def test_custom_default_value_source_can_be_registered(self):
        def custom_default_source(*, field, config, context, runtime_env, options):
            return f"{config['prefix']}-{field['key']}-{context['tenant']}"

        register_default_value_source("custom-default", custom_default_source)
        self.addCleanup(unregister_default_value_source, "custom-default")

        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "code",
                        "default_config": {
                            "source_type": "custom-default",
                            "prefix": "tenant",
                        },
                    }
                ]
            },
            context={"tenant": "acme"},
            node_code="NODE_A",
        )

        self.assertEqual(resolved_form_data["code"], "tenant-code-acme")

    def test_custom_field_options_source_can_be_registered(self):
        def custom_options_source(*, field, config, context, runtime_env):
            return [
                {"label": f"{context['tenant']}-A", "value": "a"},
                {"label": f"{context['tenant']}-B", "value": "b"},
            ]

        register_field_options_source("custom-options", custom_options_source)
        self.addCleanup(unregister_field_options_source, "custom-options")

        resolved_schema, _ = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "tenant_option",
                        "component": "select",
                        "options_config": {
                            "source_type": "custom-options",
                        },
                    }
                ]
            },
            context={"tenant": "acme"},
            node_code="NODE_A",
        )

        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [
                {"label": "acme-A", "value": "a"},
                {"label": "acme-B", "value": "b"},
            ],
        )

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.RuntimeEchoDataSource",
        ]
    )
    def test_new_default_source_config_has_priority_and_receives_runtime_context(self):
        request = SimpleNamespace(trace_token="req-1")
        instance = SimpleNamespace(id=42)

        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "code",
                        "default_config": {
                            "source_type": "context",
                            "context_path": "legacy.code",
                        },
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "runtime-echo",
                            "source_params": {"prefix": "new"},
                        },
                    }
                ]
            },
            context={"tenant": "acme", "legacy": {"code": "legacy-value"}},
            node_code="NODE_DS",
            runtime_env={"business_id": "ORD-9"},
            request=request,
            instance=instance,
        )

        self.assertEqual(
            resolved_form_data["code"],
            "new-NODE_DS-acme-req-1-42-ORD-9",
        )

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.RuntimeEchoDataSource",
        ]
    )
    def test_new_options_source_config_has_priority_over_legacy_options_config(self):
        request = SimpleNamespace(trace_token="req-2")
        instance = SimpleNamespace(id=7)

        resolved_schema, _ = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "tenant_option",
                        "component": "select",
                        "options": [{"label": "manual", "value": "manual"}],
                        "options_config": {
                            "source_type": "context",
                            "context_path": "legacy.options",
                        },
                        "options_source_config": {
                            "mode": "data_source",
                            "source_key": "runtime-echo",
                            "source_params": {"suffix": "tail"},
                        },
                    }
                ]
            },
            context={
                "tenant": "acme",
                "legacy": {"options": [{"label": "legacy", "value": "legacy"}]},
            },
            node_code="NODE_OP",
            request=request,
            instance=instance,
        )

        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [
                {"label": "NODE_OP-tail", "value": "acme", "default": False},
                {"label": "req-2", "value": 7, "default": False},
            ],
        )

    def test_builtin_order_status_data_source_resolves_enum_value(self):
        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "status",
                        "component": "select",
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "order_status",
                            "source_params": {"default_name": "CONFIRMED"},
                        },
                    }
                ]
            },
            context={},
            node_code="NODE_STATUS",
        )

        self.assertEqual(resolved_form_data["status"], 20)

    def test_builtin_order_status_data_source_builds_enum_options(self):
        resolved_schema, _ = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "status",
                        "component": "select",
                        "options_source_config": {
                            "mode": "data_source",
                            "source_key": "order_status",
                        },
                    }
                ]
            },
            context={},
            node_code="NODE_STATUS",
        )

        options = resolved_schema["fields"][0]["options"]
        self.assertGreaterEqual(len(options), 3)
        self.assertEqual(options[0]["value"], 0)
        self.assertTrue(any(item["value"] == 20 for item in options))
        self.assertTrue(all(set(item.keys()) == {"label", "value", "default"} for item in options))

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.RuntimeEchoDataSource",
        ]
    )
    def test_missing_new_source_config_falls_back_to_legacy_configs(self):
        resolved_schema, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "status",
                        "component": "select",
                        "options": [{"label": "manual", "value": "manual"}],
                        "default_config": {
                            "source_type": "context",
                            "context_path": "legacy.status",
                        },
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "missing-source",
                        },
                        "options_config": {
                            "source_type": "context",
                            "context_path": "legacy.options",
                        },
                        "options_source_config": {
                            "mode": "data_source",
                            "source_key": "missing-source",
                        },
                    }
                ]
            },
            context={
                "legacy": {
                    "status": "published",
                    "options": [{"label": "legacy", "value": "legacy"}],
                }
            },
            node_code="NODE_A",
        )

        self.assertEqual(resolved_form_data["status"], "published")
        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [{"label": "legacy", "value": "legacy", "default": False}],
        )

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.BlankDefaultDataSource",
        ]
    )
    def test_new_default_source_config_uses_fallback_value_when_data_source_returns_blank(self):
        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "code",
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "blank-default",
                            "fallback_value": "fallback-code",
                        },
                        "default_config": {
                            "source_type": "context",
                            "context_path": "legacy.code",
                        },
                    }
                ]
            },
            context={"legacy": {"code": "legacy-value"}},
            node_code="NODE_A",
        )

        self.assertEqual(resolved_form_data["code"], "fallback-code")

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.ExplodingDefaultDataSource",
        ]
    )
    def test_new_default_source_config_failure_prefers_fallback_value(self):
        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "code",
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "exploding-default",
                            "fallback_value": "fallback-code",
                        },
                        "default_config": {
                            "source_type": "context",
                            "context_path": "legacy.code",
                        },
                    }
                ]
            },
            context={"legacy": {"code": "legacy-value"}},
            node_code="NODE_A",
        )

        self.assertEqual(resolved_form_data["code"], "fallback-code")

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.ExplodingDefaultDataSource",
        ]
    )
    def test_new_default_source_config_failure_falls_back_to_legacy_default_config_without_fallback_value(self):
        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "code",
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "exploding-default",
                        },
                        "default_config": {
                            "source_type": "context",
                            "context_path": "legacy.code",
                        },
                    }
                ]
            },
            context={"legacy": {"code": "legacy-value"}},
            node_code="NODE_A",
        )

        self.assertEqual(resolved_form_data["code"], "legacy-value")

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.BlankOptionsDataSource",
        ]
    )
    def test_new_options_source_config_falls_back_to_legacy_options_config_before_manual_options(self):
        resolved_schema, _ = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "address",
                        "component": "select",
                        "options": [{"label": "manual", "value": "manual"}],
                        "options_source_config": {
                            "mode": "data_source",
                            "source_key": "blank-options",
                        },
                        "options_config": {
                            "source_type": "context",
                            "context_path": "legacy.addresses",
                        },
                    }
                ]
            },
            context={
                "legacy": {
                    "addresses": [
                        {"label": "legacy-1", "value": "legacy-1"},
                        {"label": "legacy-2", "value": "legacy-2"},
                    ]
                }
            },
            node_code="NODE_OPT",
        )

        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [
                {"label": "legacy-1", "value": "legacy-1", "default": False},
                {"label": "legacy-2", "value": "legacy-2", "default": False},
            ],
        )

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.ExplodingOptionsDataSource",
        ]
    )
    def test_new_options_source_config_failure_returns_empty_list_when_manual_fallback_disabled(self):
        resolved_schema, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "address",
                        "component": "select",
                        "options": [{"label": "manual", "value": "manual"}],
                        "options_source_config": {
                            "mode": "data_source",
                            "source_key": "exploding-options",
                            "fallback_to_manual": False,
                        },
                    }
                ]
            },
            context={},
            node_code="NODE_OPT",
        )

        self.assertEqual(resolved_schema["fields"][0]["options"], [])
        self.assertEqual(resolved_form_data["address"], "")

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.ExplodingOptionsDataSource",
        ]
    )
    def test_new_options_source_config_failure_falls_back_to_manual_options_when_enabled(self):
        resolved_schema, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "address",
                        "component": "select",
                        "options": [{"label": "manual", "value": "manual"}],
                        "options_source_config": {
                            "mode": "data_source",
                            "source_key": "exploding-options",
                            "fallback_to_manual": True,
                        },
                    }
                ]
            },
            context={},
            node_code="NODE_OPT",
        )

        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [{"label": "manual", "value": "manual", "default": False}],
        )
        self.assertEqual(resolved_form_data["address"], "")

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.ExplodingOptionsDataSource",
        ]
    )
    def test_new_options_source_config_failure_falls_back_to_legacy_options_config(self):
        resolved_schema, _ = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "address",
                        "component": "select",
                        "options": [{"label": "manual", "value": "manual"}],
                        "options_source_config": {
                            "mode": "data_source",
                            "source_key": "exploding-options",
                        },
                        "options_config": {
                            "source_type": "context",
                            "context_path": "legacy.addresses",
                        },
                    }
                ]
            },
            context={
                "legacy": {
                    "addresses": [
                        {"label": "legacy-1", "value": "legacy-1"},
                        {"label": "legacy-2", "value": "legacy-2"},
                    ]
                }
            },
            node_code="NODE_OPT",
        )

        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [
                {"label": "legacy-1", "value": "legacy-1", "default": False},
                {"label": "legacy-2", "value": "legacy-2", "default": False},
            ],
        )

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.SchemaAwareDefaultDataSource",
        ]
    )
    def test_new_default_source_config_receives_field_schema_and_source_params(self):
        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "site_address",
                        "component": "input",
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "schema-aware-default",
                            "source_params": {"token": "cfg-token"},
                        },
                    }
                ]
            },
            context={"tenant": "acme"},
            node_code="NODE_CTX",
            runtime_env={"business_id": "ORD-10"},
        )

        self.assertEqual(resolved_form_data["site_address"], "site_address|cfg-token|NODE_CTX|acme|ORD-10")

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.InjectedRequestDataSource",
        ]
    )
    def test_new_default_source_config_exposes_request_on_runtime_instance(self):
        request = SimpleNamespace(trace_token="req-self")
        instance = SimpleNamespace(id=99)

        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "ticket_code",
                        "component": "input",
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "injected-request-default",
                        },
                    }
                ]
            },
            context={"tenant": "acme"},
            node_code="NODE_REQ",
            request=request,
            instance=instance,
        )

        self.assertEqual(resolved_form_data["ticket_code"], "req-self|ticket_code|99|NODE_REQ|acme")

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.InjectedInstanceDataSource",
        ]
    )
    def test_new_default_source_config_exposes_flow_instance_on_runtime_instance(self):
        instance = SimpleNamespace(id=101, business_id="ORD-101")

        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "instance_code",
                        "component": "input",
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "injected-instance-default",
                        },
                    }
                ]
            },
            context={"tenant": "acme"},
            node_code="NODE_INSTANCE",
            instance=instance,
        )

        self.assertEqual(
            resolved_form_data["instance_code"],
            "101|ORD-101|NODE_INSTANCE|instance_code|acme",
        )

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.InjectedOptionsDataSource",
        ]
    )
    def test_new_options_source_config_exposes_runtime_injections_on_runtime_instance(self):
        request = SimpleNamespace(trace_token="req-opt")
        instance = SimpleNamespace(id=202)

        resolved_schema, _ = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "site_selector",
                        "component": "select",
                        "options_source_config": {
                            "mode": "data_source",
                            "source_key": "injected-options",
                            "source_params": {"token": "cfg-opt"},
                        },
                    }
                ]
            },
            context={"tenant": "acme"},
            node_code="NODE_OPTIONS",
            request=request,
            instance=instance,
            runtime_env={"business_id": "ORD-202"},
        )

        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [
                {
                    "label": "acme|req-opt|site_selector|202|NODE_OPTIONS|ORD-202|cfg-opt",
                    "value": "runtime-option",
                    "default": False,
                }
            ],
        )

    def test_legacy_default_config_failure_falls_back_to_field_default(self):
        def exploding_default_source(*, field, config, context, runtime_env, options):
            raise RuntimeError("legacy default failed")

        register_default_value_source("exploding-default", exploding_default_source)
        self.addCleanup(unregister_default_value_source, "exploding-default")

        _, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "code",
                        "default": "field-default",
                        "default_config": {
                            "source_type": "exploding-default",
                        },
                    }
                ]
            },
            context={},
            node_code="NODE_A",
        )

        self.assertEqual(resolved_form_data["code"], "field-default")

    def test_legacy_options_config_failure_falls_back_to_manual_options(self):
        def exploding_options_source(*, field, config, context, runtime_env):
            raise RuntimeError("legacy options failed")

        register_field_options_source("exploding-options", exploding_options_source)
        self.addCleanup(unregister_field_options_source, "exploding-options")

        resolved_schema, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "key": "address",
                        "component": "select",
                        "options": [{"label": "manual", "value": "manual"}],
                        "options_config": {
                            "source_type": "exploding-options",
                            "fallback_to_manual": True,
                        },
                    }
                ]
            },
            context={},
            node_code="NODE_A",
        )

        self.assertEqual(
            resolved_schema["fields"][0]["options"],
            [{"label": "manual", "value": "manual", "default": False}],
        )
        self.assertEqual(resolved_form_data["address"], "")

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.TextContentDataSource",
        ]
    )
    def test_text_component_can_resolve_content_from_default_data_source(self):
        resolved_schema, resolved_form_data = resolve_form_runtime(
            form_schema={
                "fields": [
                    {
                        "component": "paragraph",
                        "label": "说明",
                        "content": "原始内容",
                        "default_source_config": {
                            "mode": "data_source",
                            "source_key": "text-content",
                            "source_params": {"prefix": "notice"},
                        },
                    }
                ]
            },
            context={"tenant": "acme"},
            node_code="NODE_TEXT",
        )

        self.assertEqual(resolved_schema["fields"][0]["content"], "notice|acme|NODE_TEXT")
        self.assertEqual(resolved_form_data, {})

    def test_context_binding_write_target_controls_update_scope(self):
        updates = build_context_updates_from_form_data(
            form_schema={
                "fields": [
                    {"key": "skip_me", "context_binding": {"write_target": "none"}},
                    {"key": "flow_only", "context_binding": {"write_target": "flow"}},
                    {"key": "node_only", "context_binding": {"write_target": "node"}},
                    {"key": "both_ctx", "context_binding": {"write_target": "both"}},
                ]
            },
            form_data={
                "skip_me": "A",
                "flow_only": "B",
                "node_only": "C",
                "both_ctx": "D",
            },
            existing_context={},
            node_code="NODE_A",
        )

        self.assertEqual(updates["flow_only"], "B")
        self.assertEqual(updates["form"]["NODE_A"]["node_only"], "C")
        self.assertEqual(updates["both_ctx"], "D")
        self.assertEqual(updates["form"]["NODE_A"]["both_ctx"], "D")
        self.assertNotIn("skip_me", updates)

    def test_context_binding_merge_if_absent_applies_per_target(self):
        updates = build_context_updates_from_form_data(
            form_schema={
                "fields": [
                    {
                        "key": "both_ctx",
                        "context_binding": {
                            "write_target": "both",
                            "write_mode": "merge_if_absent",
                        },
                    }
                ]
            },
            form_data={"both_ctx": "NEW"},
            existing_context={
                "both_ctx": "OLD_FLOW",
                "form": {"NODE_A": {"both_ctx": ""}},
            },
            node_code="NODE_A",
        )

        self.assertNotIn("both_ctx", updates)
        self.assertEqual(updates["form"]["NODE_A"]["both_ctx"], "NEW")


class BuiltinDataSourceExamplesTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _extract_json_script_payload(self, content: str, script_id: str):
        matched = re.search(
            rf'<script id="{re.escape(script_id)}" type="application/json">(.*?)</script>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(matched, f"missing json_script payload: {script_id}")
        return json.loads(matched.group(1))

    def test_flow_designer_options_source_only_shows_fixed_options_and_data_source(self):
        content = get_template("flow_engine/flow_designer.html").template.source

        self.assertIn("选项来源", content)
        self.assertIn("固定选项", content)
        self.assertIn("数据源类", content)
        self.assertNotIn("手工维护", content)

    def test_form_designer_options_source_only_shows_fixed_options_and_data_source(self):
        content = get_template("flow_engine/form_designer/index.html").template.source

        self.assertIn("选项来源", content)
        self.assertIn("固定选项", content)
        self.assertIn("数据源类", content)
        self.assertNotIn("手工维护", content)

    def test_form_list_page_uses_global_form_library_list_endpoint(self):
        content = get_template("flow_engine/form_list.html").template.source

        self.assertIn("/flow_engine/form_library_global_list", content)
        self.assertNotIn("/flow_engine/flow_definition_page_list", content)
        self.assertIn("表单分组", content)
        self.assertNotIn("所属流程", content)

    def test_builtin_examples_include_at_least_three_designer_ready_examples(self):
        examples = get_builtin_form_data_source_examples()

        self.assertGreaterEqual(len(examples), 3)
        self.assertGreaterEqual(len({item["code"] for item in examples}), 3)
        self.assertTrue(any(item["target"] == "default" for item in examples))
        self.assertTrue(any(item["target"] == "options" for item in examples))
        for item in examples:
            self.assertTrue(item["source_key"])
            self.assertRegex(item["title"], r"[\u4e00-\u9fff]")
            self.assertRegex(item["description"], r"[\u4e00-\u9fff]")
            self.assertEqual(item["config"]["mode"], "data_source")
            self.assertEqual(item["config"]["source_key"], item["source_key"])
            self.assertIn("source_params", item["config"])

    def test_builtin_examples_reference_registered_builtin_data_sources(self):
        examples = get_builtin_form_data_source_examples()
        source_keys = {item["key"] for item in get_registered_field_data_source_metadata()}

        self.assertTrue(source_keys)
        for item in examples:
            self.assertIn(item["source_key"], source_keys)

    def test_builtin_examples_return_deep_copied_configs(self):
        examples = get_builtin_form_data_source_examples()
        examples[0]["config"]["source_params"]["default_name"] = "MUTATED"

        latest = get_builtin_form_data_source_examples()

        self.assertNotEqual(latest[0]["config"]["source_params"].get("default_name"), "MUTATED")

    def test_flow_designer_page_includes_builtin_examples_context(self):
        request = self.factory.get("/admin/flow_engine/definition/add/")
        request.user = AnonymousUser()
        with patch("flow_engine.page_views.flow_page.render") as mocked_render:
            flow_definition_add(request)

        args, _ = mocked_render.call_args
        context = args[2]
        self.assertEqual(args[1], "flow_engine/flow_designer.html")
        self.assertIn("builtin_data_source_examples", context)
        self.assertIn("field_data_source_metadata", context)
        codes = {item["code"] for item in context["builtin_data_source_examples"]}
        self.assertIn("options.db.site_address_by_order", codes)
        source_keys = {item["key"] for item in context["field_data_source_metadata"]}
        self.assertIn("order_status", source_keys)
        self.assertIn("site_address_select", source_keys)

    def test_form_designer_page_includes_builtin_examples_context(self):
        request = self.factory.get("/admin/flow_engine/definition/1/form_designer/")
        request.user = AnonymousUser()
        with patch("flow_engine.page_views.flow_page.render") as mocked_render:
            flow_form_designer(request, fid=1)

        args, _ = mocked_render.call_args
        context = args[2]
        self.assertEqual(args[1], "flow_engine/form_designer/index.html")
        self.assertIn("builtin_data_source_examples", context)
        self.assertIn("field_data_source_metadata", context)
        codes = {item["code"] for item in context["builtin_data_source_examples"]}
        self.assertIn("default.enum.order_status", codes)
        self.assertIn("options.enum.order_status", codes)
        source_keys = {item["key"] for item in context["field_data_source_metadata"]}
        self.assertIn("order_status", source_keys)
        self.assertIn("site_address_select", source_keys)

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.RuntimeEchoDataSource",
        ]
    )
    def test_flow_designer_page_renders_field_data_source_metadata_json_for_bootstrap(self):
        request = self.factory.get("/admin/flow_engine/definition/add/")
        request.user = AnonymousUser()

        with patch("simpleui.templatetags.simpletags.get_model_url", return_value=""):
            response = flow_definition_add(request)
        content = response.content.decode("utf-8")
        metadata = self._extract_json_script_payload(content, "field-data-source-metadata")
        by_key = {item["key"]: item for item in metadata}

        self.assertEqual(response.status_code, 200)
        self.assertIn('document.getElementById("field-data-source-metadata")?.textContent || "[]"', content)
        self.assertIn("runtime-echo", by_key)
        self.assertEqual(by_key["runtime-echo"]["label"], "Runtime Echo")
        self.assertEqual(
            set(by_key["runtime-echo"]["supported_methods"]),
            {"get_default_text", "get_options_options"},
        )

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.RuntimeEchoDataSource",
        ]
    )
    def test_form_designer_page_renders_field_data_source_metadata_json_for_bootstrap(self):
        request = self.factory.get("/admin/flow_engine/definition/1/form_designer/")
        request.user = AnonymousUser()

        response = flow_form_designer(request, fid=1)
        content = response.content.decode("utf-8")
        metadata = self._extract_json_script_payload(content, "field-data-source-metadata")
        by_key = {item["key"]: item for item in metadata}

        self.assertEqual(response.status_code, 200)
        self.assertIn('document.getElementById("field-data-source-metadata")?.textContent || "[]"', content)
        self.assertIn("runtime-echo", by_key)
        self.assertEqual(by_key["runtime-echo"]["data_type"], "text")
        self.assertEqual(by_key["runtime-echo"]["support_components"], ["input", "textarea", "select"])


class FieldDataSourceMetadataApiTests(SimpleTestCase):
    REQUIRED_METADATA_KEYS = {
        "key",
        "label",
        "data_type",
        "support_components",
        "supported_methods",
    }

    def setUp(self):
        self.factory = RequestFactory()

    def test_registered_field_data_source_metadata_includes_builtin_sources(self):
        items = get_registered_field_data_source_metadata()

        by_key = {item["key"]: item for item in items}
        self.assertIn("order_status", by_key)
        self.assertIn("site_address_select", by_key)
        self.assertEqual(by_key["order_status"]["data_type"], "select")
        self.assertEqual(by_key["site_address_select"]["data_type"], "select")
        self.assertEqual(by_key["site_address_select"]["support_components"], ["select", "radio", "checkbox"])
        self.assertEqual(
            set(by_key["order_status"]["supported_methods"]),
            {"get_default_text", "get_default_number", "get_default_options", "get_options_options"},
        )
        self.assertEqual(by_key["site_address_select"]["supported_methods"], ["get_options_options"])
        for item in items:
            self.assertEqual(set(item.keys()), self.REQUIRED_METADATA_KEYS)

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.RuntimeEchoDataSource",
        ]
    )
    def test_metadata_api_returns_registered_custom_source(self):
        request = self.factory.get("/admin/flow_engine/field_data_sources/metadata/")
        response = field_data_source_metadata(request)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        by_key = {item["key"]: item for item in payload["items"]}
        self.assertIn("runtime-echo", by_key)
        self.assertEqual(by_key["runtime-echo"]["label"], "Runtime Echo")
        self.assertEqual(by_key["runtime-echo"]["data_type"], "text")
        self.assertEqual(by_key["runtime-echo"]["support_components"], ["input", "textarea", "select"])
        self.assertEqual(
            set(by_key["runtime-echo"]["supported_methods"]),
            {"get_default_text", "get_options_options"},
        )
        self.assertEqual(set(by_key["runtime-echo"].keys()), self.REQUIRED_METADATA_KEYS)

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.RuntimeEchoDataSource",
        ]
    )
    def test_standard_api_view_returns_same_metadata_payload_as_page_json_endpoint(self):
        request = self.factory.get("/api/flow_engine/field_data_source_metadata/")
        request.user = AnonymousUser()

        api_response = async_to_sync(FieldDataSourceMetadataApiView.api)(request)
        page_response = field_data_source_metadata(
            self.factory.get("/admin/flow_engine/field_data_sources/metadata/")
        )

        self.assertEqual(api_response.data.model_dump(), json.loads(page_response.content))
        by_key = {item.key: item for item in api_response.data.items}
        self.assertIn("runtime-echo", by_key)
        self.assertEqual(by_key["runtime-echo"].label, "Runtime Echo")
        self.assertEqual(
            set(api_response.data.model_dump()["items"][0].keys()),
            self.REQUIRED_METADATA_KEYS,
        )

    def test_standard_api_view_uses_chinese_failure_message(self):
        self.assertEqual(
            FieldDataSourceMetadataApiView.finally_code,
            ("000", "查询字段数据源元数据失败"),
        )


class RuntimeFieldDataSourceRegistryTests(SimpleTestCase):
    def test_legacy_and_new_import_paths_reference_same_classes(self):
        self.assertIs(BaseFieldDataSource, NewBaseFieldDataSource)
        self.assertIs(RuntimeFieldDataSourceRegistry, NewRuntimeFieldDataSourceRegistry)

    def test_register_builtin_requires_non_empty_key(self):
        registry = RuntimeFieldDataSourceRegistry()

        class MissingKeyDataSource(BaseFieldDataSource):
            pass

        with self.assertRaisesMessage(ValueError, "field data source key is required"):
            registry.register_builtin(MissingKeyDataSource)

    def test_register_builtin_requires_non_empty_label(self):
        registry = RuntimeFieldDataSourceRegistry()

        class MissingLabelDataSource(BaseFieldDataSource):
            key = "missing-label"
            data_type = "text"
            support_components = ["input"]

            def get_default_text(self):
                return "ok"

        with self.assertRaisesMessage(
            ValueError,
            "field data source 'missing-label' must define a non-empty label",
        ):
            registry.register_builtin(MissingLabelDataSource)

    def test_register_builtin_requires_base_class(self):
        registry = RuntimeFieldDataSourceRegistry()

        class NotADataSource:
            key = "bad-source"
            data_type = "text"
            support_components = ["input"]

        with self.assertRaisesMessage(ValueError, "field data source must inherit BaseFieldDataSource"):
            registry.register_builtin(NotADataSource)

    def test_register_builtin_rejects_duplicate_key(self):
        registry = RuntimeFieldDataSourceRegistry()

        class SourceA(BaseFieldDataSource):
            key = "dup-source"
            label = "Duplicate Source A"
            data_type = "text"
            support_components = ["input"]

            def get_default_text(self):
                return "a"

        class SourceB(BaseFieldDataSource):
            key = "dup-source"
            label = "Duplicate Source B"
            data_type = "text"
            support_components = ["textarea"]

            def get_default_text(self):
                return "b"

        registry.register_builtin(SourceA)
        with self.assertRaisesMessage(ValueError, "field data source key 'dup-source' is already registered"):
            registry.register_builtin(SourceB)

    def test_register_builtin_requires_valid_data_type(self):
        registry = RuntimeFieldDataSourceRegistry()

        class InvalidTypeSource(BaseFieldDataSource):
            key = "invalid-type"
            label = "Invalid Type"
            data_type = "bad-type"
            support_components = ["input"]

            def get_default_text(self):
                return "ok"

        with self.assertRaisesMessage(ValueError, "field data source 'invalid-type' has invalid data_type 'bad-type'"):
            registry.register_builtin(InvalidTypeSource)

    def test_register_builtin_requires_valid_support_components(self):
        registry = RuntimeFieldDataSourceRegistry()

        class InvalidComponentSource(BaseFieldDataSource):
            key = "invalid-component"
            label = "Invalid Component"
            data_type = "text"
            support_components = ["input", "grid"]

            def get_default_text(self):
                return "ok"

        with self.assertRaisesMessage(
            ValueError,
            "field data source 'invalid-component' has invalid support_components: grid",
        ):
            registry.register_builtin(InvalidComponentSource)

    def test_register_builtin_requires_at_least_one_datasource_method(self):
        registry = RuntimeFieldDataSourceRegistry()

        class NoMethodSource(BaseFieldDataSource):
            key = "no-method"
            label = "No Method"
            data_type = "text"
            support_components = ["input"]

        with self.assertRaisesMessage(
            ValueError,
            "field data source 'no-method' must implement at least one datasource method",
        ):
            registry.register_builtin(NoMethodSource)

    def test_register_builtin_requires_component_compatible_method(self):
        registry = RuntimeFieldDataSourceRegistry()

        class IncompatibleMethodSource(BaseFieldDataSource):
            key = "incompatible-method"
            label = "Incompatible Method"
            data_type = "text"
            support_components = ["input"]

            def get_options_options(self):
                return []

        with self.assertRaisesMessage(
            ValueError,
            "field data source 'incompatible-method' does not implement any datasource method for its support_components",
        ):
            registry.register_builtin(IncompatibleMethodSource)

    @override_settings(FLOW_ENGINE_FIELD_DATA_SOURCES=[])
    def test_metadata_returns_sorted_items_and_defensive_copies(self):
        registry = RuntimeFieldDataSourceRegistry()

        class ZSource(BaseFieldDataSource):
            key = "z_source"
            label = "Z Source"
            data_type = "text"
            support_components = [" input ", "", None]

            def get_default_text(self):
                return "z"

        class ASource(BaseFieldDataSource):
            key = "a_source"
            label = "A Source"
            data_type = "select"
            support_components = ["select"]

            def get_options_options(self):
                return [{"label": "A", "value": "a"}]

        registry.register_builtin(ZSource)
        registry.register_builtin(ASource)

        items = registry.metadata()
        self.assertEqual([item["key"] for item in items], ["a_source", "z_source"])
        self.assertEqual(items[1]["support_components"], ["input"])
        self.assertEqual(items[0]["supported_methods"], ["get_options_options"])

        items[0]["supported_methods"][0] = "mutated"
        latest = registry.metadata()
        self.assertEqual(latest[0]["supported_methods"], ["get_options_options"])

    def test_base_field_data_source_supports_bind_runtime(self):
        source = BaseFieldDataSource()
        returned = source.bind_runtime(
            ctx={"tenant": "acme"},
            request=SimpleNamespace(trace_token="req-9"),
            field_schema={"key": "code"},
            instance=SimpleNamespace(id=1),
            node_code="NODE_X",
            runtime_env={"business_id": "ORD-1"},
            source_config={"source_key": "demo", "source_params": {"prefix": "v"}},
            source_params={"prefix": "v"},
            component="input",
            target="default",
        )

        self.assertIs(returned, source)
        self.assertEqual(source.ctx, {"tenant": "acme"})
        self.assertEqual(source.field_schema, {"key": "code"})
        self.assertEqual(source.node_code, "NODE_X")
        self.assertEqual(source.source_config["source_key"], "demo")
        self.assertEqual(source.source_params, {"prefix": "v"})
        self.assertEqual(source.component, "input")
        self.assertEqual(source.target, "default")

    @override_settings(FLOW_ENGINE_FIELD_DATA_SOURCES=["flow_engine.tests.RuntimeEchoDataSource"])
    def test_settings_data_sources_are_loaded(self):
        registry = RuntimeFieldDataSourceRegistry()

        self.assertIs(registry.get("runtime-echo"), RuntimeEchoDataSource)

    @override_settings(FLOW_ENGINE_FIELD_DATA_SOURCES=["flow_engine.tests.RuntimeEchoDataSource"])
    def test_settings_duplicate_key_against_builtin_raises_error(self):
        registry = RuntimeFieldDataSourceRegistry()

        class BuiltinSource(BaseFieldDataSource):
            key = "runtime-echo"
            label = "Builtin Runtime Echo"
            data_type = "text"
            support_components = ["input"]

            def get_default_text(self):
                return "builtin"

        registry.register_builtin(BuiltinSource)

        with self.assertRaisesMessage(ImproperlyConfigured, "field data source key 'runtime-echo' is duplicated"):
            registry.metadata()

    @override_settings(FLOW_ENGINE_FIELD_DATA_SOURCES=["django.test.SimpleTestCase"])
    def test_settings_require_base_class(self):
        registry = RuntimeFieldDataSourceRegistry()

        with self.assertRaisesMessage(ImproperlyConfigured, "field data source must inherit BaseFieldDataSource"):
            registry.metadata()

    @override_settings(FLOW_ENGINE_FIELD_DATA_SOURCES=["flow_engine.tests.RuntimeEchoDataSource"])
    def test_get_normalizes_key_for_settings_sources(self):
        registry = RuntimeFieldDataSourceRegistry()

        self.assertIs(registry.get("  RUNTIME-ECHO  "), RuntimeEchoDataSource)
        self.assertIsNone(registry.get("   "))

    @override_settings(FLOW_ENGINE_FIELD_DATA_SOURCES=["flow_engine.tests.RuntimeEchoDataSource"])
    def test_all_returns_combined_mapping_copy(self):
        registry = RuntimeFieldDataSourceRegistry()

        class BuiltinOnlySource(BaseFieldDataSource):
            key = "builtin-only"
            label = "Builtin Only"
            data_type = "text"
            support_components = ["input"]

            def get_default_text(self):
                return "builtin-only"

        registry.register_builtin(BuiltinOnlySource)

        combined = registry.all()
        self.assertEqual(set(combined), {"builtin-only", "runtime-echo"})
        self.assertIs(combined["builtin-only"], BuiltinOnlySource)
        self.assertIs(combined["runtime-echo"], RuntimeEchoDataSource)

        combined.pop("builtin-only")
        self.assertIs(registry.get("builtin-only"), BuiltinOnlySource)

    def test_build_returns_instance_with_runtime_kwargs(self):
        registry = RuntimeFieldDataSourceRegistry()
        request = SimpleNamespace(trace_token="trace-1")
        instance = SimpleNamespace(id=99)

        class BuildableSource(BaseFieldDataSource):
            key = "buildable"
            label = "Buildable"
            data_type = "text"
            support_components = ["input"]

            def get_default_text(self):
                return "ok"

        registry.register_builtin(BuildableSource)

        source = registry.build(
            "BUILDABLE",
            ctx={"tenant": "alpha"},
            request=request,
            field_schema={"default_source_config": {"source_params": {"prefix": "p"}}},
            instance=instance,
            node_code="node_a",
            runtime_env={"business_id": "biz-1"},
            source_config={"source_key": "buildable", "source_params": {"prefix": "p"}},
            source_params={"prefix": "p"},
            component="input",
            target="default",
        )
        self.assertIsInstance(source, BuildableSource)
        self.assertEqual(source.ctx, {"tenant": "alpha"})
        self.assertIs(source.request, request)
        self.assertEqual(source.field_schema["default_source_config"]["source_params"]["prefix"], "p")
        self.assertIs(source.instance, instance)
        self.assertEqual(source.node_code, "node_a")
        self.assertEqual(source.runtime_env, {"business_id": "biz-1"})
        self.assertEqual(source.source_params, {"prefix": "p"})
        self.assertEqual(source.component, "input")
        self.assertEqual(source.target, "default")
        self.assertIsNone(registry.build("missing", ctx={}))

    @override_settings(FLOW_ENGINE_FIELD_DATA_SOURCES=["does.not.exist.DataSource"])
    def test_settings_invalid_import_raises_configured_error(self):
        registry = RuntimeFieldDataSourceRegistry()

        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "FLOW_ENGINE_FIELD_DATA_SOURCES contains an invalid import: does.not.exist.DataSource",
        ):
            registry.all()

    @override_settings(
        FLOW_ENGINE_FIELD_DATA_SOURCES=[
            "flow_engine.tests.RuntimeEchoDataSource",
            "flow_engine.tests.RuntimeEchoDataSource",
        ]
    )
    def test_settings_duplicate_key_within_settings_raises_error(self):
        registry = RuntimeFieldDataSourceRegistry()

        with self.assertRaisesMessage(ImproperlyConfigured, "field data source key 'runtime-echo' is duplicated"):
            registry.all()

