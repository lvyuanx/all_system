from django.test import SimpleTestCase

from flow_engine.utils.form_runtime_util import (
    register_default_value_source,
    register_field_options_source,
    resolve_form_runtime,
    unregister_default_value_source,
    unregister_field_options_source,
)


class FormRuntimeDataSourceRegistryTests(SimpleTestCase):
    def test_legacy_default_config_and_manual_options_still_work(self):
        schema = {
            "fields": [
                {
                    "key": "status",
                    "component": "select",
                    "options": [
                        {"label": "草稿", "value": "draft"},
                        {"label": "已发布", "value": "published"},
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
                {"label": "草稿", "value": "draft", "default": False},
                {"label": "已发布", "value": "published", "default": False},
            ],
        )

    def test_legacy_options_config_falls_back_to_manual_options(self):
        schema = {
            "fields": [
                {
                    "key": "address",
                    "component": "select",
                    "options": [
                        {"label": "默认地址", "value": 1},
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
            [{"label": "默认地址", "value": 1, "default": False}],
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
