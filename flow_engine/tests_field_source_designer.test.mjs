import test from "node:test";
import assert from "node:assert/strict";

import {
    buildDefaultSourcePayload,
    buildOptionsSourcePayload,
    getAvailableFieldDataSources,
    getFieldSourceParamSchema,
    normalizeDefaultSourceUi,
    normalizeFieldDataSourceMetadata,
    normalizeOptionsSourceUi,
    shouldUseManualOptions,
    syncFieldSourceParamsBySchema,
} from "../oss/static/flow_engine/js/field_source_designer.js";

const metadata = normalizeFieldDataSourceMetadata([
    {
        key: "ctx_text",
        label: "Context Text",
        data_type: "text",
        support_components: ["input", "textarea"],
        support_default: true,
        support_options: false,
        params_schema: [
            { name: "context_path", label: "路径", target: "default", component: "input" },
        ],
    },
    {
        key: "site_address_select",
        label: "Site Address",
        data_type: "select",
        support_components: ["select", "radio"],
        support_default: false,
        support_options: true,
        params_schema: [
            { name: "order_id_path", label: "订单路径", target: "options", component: "input" },
        ],
    },
]);

test("normalizes new default source config before legacy config", () => {
    const field = {
        default: "",
        default_config: {
            source_type: "context",
            context_path: "legacy.code",
        },
        default_source_config: {
            mode: "data_source",
            source_key: "ctx_text",
            source_params: {
                context_path: "form.current.code",
            },
            fallback_value: "N/A",
        },
    };

    const ui = normalizeDefaultSourceUi(field, field.default);
    assert.equal(ui.mode, "data_source");
    assert.equal(ui.source_key, "ctx_text");
    assert.deepEqual(ui.source_params, { context_path: "form.current.code" });
    assert.equal(ui.fallback_value, "N/A");
    assert.deepEqual(ui.legacy_config, {
        source_type: "context",
        value: "",
        context_path: "legacy.code",
        enum_code: "",
        db_source_code: "",
        fallback_value: "",
    });
});

test("preserves legacy options config and manual fallback semantics", () => {
    const field = {
        options_config: {
            source_type: "context",
            context_path: "legacy.options",
            fallback_to_manual: true,
        },
    };

    const ui = normalizeOptionsSourceUi(field);
    assert.equal(ui.mode, "legacy");
    assert.equal(shouldUseManualOptions({ options_source_ui: ui }), true);
    assert.deepEqual(ui.legacy_config, {
        source_type: "context",
        context_path: "legacy.options",
        enum_code: "",
        db_source_code: "",
        label_key: "label",
        value_key: "value",
        fallback_to_manual: true,
    });
});

test("filters metadata by target and component and syncs params by schema", () => {
    const defaultSources = getAvailableFieldDataSources(metadata, "default", "input");
    const optionSources = getAvailableFieldDataSources(metadata, "options", "select");

    assert.deepEqual(defaultSources.map((item) => item.key), ["ctx_text"]);
    assert.deepEqual(optionSources.map((item) => item.key), ["site_address_select"]);
    assert.deepEqual(getFieldSourceParamSchema(metadata, "site_address_select", "options"), [
        {
            name: "order_id_path",
            label: "订单路径",
            target: "options",
            component: "input",
            placeholder: "",
            help: "",
            options: [],
        },
    ]);
    assert.deepEqual(
        syncFieldSourceParamsBySchema(metadata, "site_address_select", "options", {
            order_id_path: "runtime.order_id",
            ignored: "x",
        }),
        { order_id_path: "runtime.order_id" },
    );
});

test("builds payloads with new config and retained legacy fallback", () => {
    const defaultPayload = buildDefaultSourcePayload({
        default: "",
        default_source_ui: {
            mode: "data_source",
            source_key: "ctx_text",
            source_params: { context_path: "form.code" },
            fallback_value: "fallback",
            legacy_config: {
                source_type: "context",
                context_path: "legacy.code",
                fallback_value: "",
            },
        },
    });
    const optionsPayload = buildOptionsSourcePayload({
        options_source_ui: {
            mode: "data_source",
            source_key: "site_address_select",
            source_params: { order_id_path: "runtime.order_id" },
            fallback_to_manual: false,
            legacy_config: {
                source_type: "context",
                context_path: "legacy.options",
                fallback_to_manual: true,
            },
        },
    });

    assert.deepEqual(defaultPayload, {
        default_source_config: {
            mode: "data_source",
            source_key: "ctx_text",
            source_params: { context_path: "form.code" },
            fallback_value: "fallback",
        },
        default_config: {
            source_type: "context",
            value: "",
            context_path: "legacy.code",
            enum_code: "",
            db_source_code: "",
            fallback_value: "",
        },
    });
    assert.deepEqual(optionsPayload, {
        options_source_config: {
            mode: "data_source",
            source_key: "site_address_select",
            source_params: { order_id_path: "runtime.order_id" },
            fallback_to_manual: false,
        },
        options_config: {
            source_type: "context",
            context_path: "legacy.options",
            enum_code: "",
            db_source_code: "",
            label_key: "label",
            value_key: "value",
            fallback_to_manual: true,
        },
    });
});
