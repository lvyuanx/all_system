import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, override_settings

from flow_engine.page_views.flow_page import (
    field_data_source_metadata,
    flow_definition_add,
    flow_form_designer,
)
from flow_engine.utils.form_designer_data_source_examples import (
    get_builtin_form_data_source_examples,
)
from flow_engine.utils.form_runtime_util import (
    BaseFieldDataSource,
    RuntimeFieldDataSourceRegistry,
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
    support_components = ["input", "textarea"]
    support_default = True
    support_options = True
    params_schema = [
        {"name": "prefix", "label": "Prefix", "target": "default", "component": "input"},
        {"name": "suffix", "label": "Suffix", "target": "options", "component": "input"},
    ]

    def get_default(self, request):
        params = self.get_source_params("default")
        request_token = getattr(request, "trace_token", "missing-request")
        instance_id = getattr(self.instance, "id", "missing-instance")
        return (
            f"{params.get('prefix', 'pfx')}-"
            f"{self.node_code}-"
            f"{self.ctx.get('tenant', '')}-"
            f"{request_token}-"
            f"{instance_id}-"
            f"{self.runtime_env.get('business_id', '')}"
        )

    def get_options(self, request):
        params = self.get_source_params("options")
        return [
            {"label": f"{self.node_code}-{params.get('suffix', 'A')}", "value": self.ctx.get("tenant", "")},
            {"label": getattr(request, "trace_token", "missing-request"), "value": getattr(self.instance, "id", "")},
        ]


class BlankDefaultDataSource(BaseFieldDataSource):
    key = "blank-default"
    label = "Blank Default"
    data_type = "text"
    support_components = ["input"]
    support_default = True

    def get_default(self, request):
        return ""


class SchemaAwareDefaultDataSource(BaseFieldDataSource):
    key = "schema-aware-default"
    label = "Schema Aware Default"
    data_type = "text"
    support_components = ["input"]
    support_default = True

    def get_default(self, request):
        return (
            f"{self.field_schema.get('key')}|"
            f"{self.get_source_params('default').get('token')}|"
            f"{self.node_code}|"
            f"{self.ctx.get('tenant')}|"
            f"{self.runtime_env.get('business_id')}"
        )


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


class BuiltinDataSourceExamplesTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_builtin_examples_include_at_least_three_designer_ready_examples(self):
        examples = get_builtin_form_data_source_examples()

        self.assertGreaterEqual(len(examples), 3)
        self.assertGreaterEqual(len({item["code"] for item in examples}), 3)
        self.assertTrue(any(item["target"] == "default" for item in examples))
        self.assertTrue(any(item["target"] == "options" for item in examples))
        for item in examples:
            self.assertIn(item["source_type"], {"context", "enum", "db"})
            self.assertEqual(item["config"]["source_type"], item["source_type"])

    def test_builtin_examples_return_deep_copied_configs(self):
        examples = get_builtin_form_data_source_examples()
        examples[0]["config"]["context_path"] = "mutated.path"

        latest = get_builtin_form_data_source_examples()

        self.assertEqual(latest[0]["config"]["context_path"], "form.NODE_A.amount")

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
        self.assertIn("default.db.order_receiver_name", codes)
        self.assertIn("options.db.site_address_by_order", codes)
        source_keys = {item["key"] for item in context["field_data_source_metadata"]}
        self.assertIn("ctx_text", source_keys)
        self.assertIn("site_address_select", source_keys)

    def test_form_designer_page_includes_builtin_examples_context(self):
        request = self.factory.get("/admin/flow_engine/definition/1/form_designer/")
        request.user = AnonymousUser()
        with patch("flow_engine.page_views.flow_page.render") as mocked_render:
            flow_form_designer(request, fid=1)

        args, _ = mocked_render.call_args
        context = args[2]
        self.assertEqual(args[1], "flow_engine/form_designer.html")
        self.assertIn("builtin_data_source_examples", context)
        self.assertIn("field_data_source_metadata", context)
        codes = {item["code"] for item in context["builtin_data_source_examples"]}
        self.assertIn("default.context.current_node_amount", codes)
        self.assertIn("options.enum.order_status", codes)
        source_keys = {item["key"] for item in context["field_data_source_metadata"]}
        self.assertIn("ctx_text", source_keys)
        self.assertIn("site_address_select", source_keys)


class FieldDataSourceMetadataApiTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_registered_field_data_source_metadata_includes_builtin_sources(self):
        items = get_registered_field_data_source_metadata()

        by_key = {item["key"]: item for item in items}
        self.assertIn("ctx_text", by_key)
        self.assertIn("order_field_text", by_key)
        self.assertIn("site_address_select", by_key)
        self.assertTrue(by_key["ctx_text"]["label"])
        self.assertEqual(by_key["site_address_select"]["data_type"], "select")
        self.assertEqual(by_key["site_address_select"]["support_components"], ["select", "radio", "checkbox"])
        self.assertTrue(by_key["ctx_text"]["support_default"])
        self.assertFalse(by_key["ctx_text"]["support_options"])
        self.assertTrue(by_key["site_address_select"]["support_options"])
        self.assertEqual(by_key["ctx_text"]["params_schema"], [])

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
        self.assertEqual(by_key["runtime-echo"]["support_components"], ["input", "textarea"])
        self.assertTrue(by_key["runtime-echo"]["support_default"])
        self.assertTrue(by_key["runtime-echo"]["support_options"])
        self.assertEqual(
            by_key["runtime-echo"]["params_schema"],
            [
                {"name": "prefix", "label": "Prefix", "target": "default", "component": "input"},
                {"name": "suffix", "label": "Suffix", "target": "options", "component": "input"},
            ],
        )


class RuntimeFieldDataSourceRegistryTests(SimpleTestCase):
    def test_register_builtin_requires_non_empty_key(self):
        registry = RuntimeFieldDataSourceRegistry()

        class MissingKeyDataSource(BaseFieldDataSource):
            pass

        with self.assertRaisesMessage(ValueError, "field data source key is required"):
            registry.register_builtin(MissingKeyDataSource)

    def test_metadata_returns_sorted_items_and_defensive_copies(self):
        registry = RuntimeFieldDataSourceRegistry()

        class ZSource(BaseFieldDataSource):
            key = "z_source"
            label = "Z Source"
            data_type = "text"
            support_components = [" input ", "", None]
            support_default = True
            params_schema = [{"name": "code", "label": "Code", "target": "default", "component": "input"}]

        class ASource(BaseFieldDataSource):
            key = "a_source"
            label = "A Source"
            data_type = "select"
            support_components = ["select"]
            support_options = True
            params_schema = [{"name": "tenant", "label": "Tenant", "target": "options", "component": "input"}]

        registry.register_builtin(ZSource)
        registry.register_builtin(ASource)

        items = registry.metadata()
        self.assertEqual([item["key"] for item in items], ["a_source", "z_source"])
        self.assertEqual(items[1]["support_components"], ["input"])

        items[0]["params_schema"][0]["label"] = "Mutated"
        latest = registry.metadata()
        self.assertEqual(latest[0]["params_schema"][0]["label"], "Tenant")
