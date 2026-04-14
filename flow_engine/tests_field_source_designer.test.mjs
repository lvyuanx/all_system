import test from "node:test";
import assert from "node:assert/strict";

import {
    buildContextBindingPayload,
    buildDefaultSourcePayload,
    buildOptionsSourcePayload,
    getAvailableFieldDataSources,
    getFieldSourceParamSchema,
    normalizeContextBindingUi,
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
        supported_methods: ["get_default_text"],
    },
    {
        key: "site_address_select",
        label: "Site Address",
        data_type: "select",
        support_components: ["select", "radio"],
        supported_methods: ["get_options_options"],
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
    assert.equal(ui.mode, "manual");
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

test("legacy default config stays hidden from the main UI but remains available for compatibility payloads", () => {
    const field = {
        default: "",
        default_config: {
            source_type: "context",
            context_path: "legacy.code",
            fallback_value: "legacy-fallback",
        },
    };

    const ui = normalizeDefaultSourceUi(field, field.default);
    assert.equal(ui.mode, "fixed");
    assert.deepEqual(ui.legacy_config, {
        source_type: "context",
        value: "",
        context_path: "legacy.code",
        enum_code: "",
        db_source_code: "",
        fallback_value: "legacy-fallback",
    });
    assert.deepEqual(buildDefaultSourcePayload({
        default: field.default,
        default_source_ui: ui,
    }), {
        default_config: {
            source_type: "context",
            value: "",
            context_path: "legacy.code",
            enum_code: "",
            db_source_code: "",
            fallback_value: "legacy-fallback",
        },
    });
});

test("legacy default config wins when non-datasource new mode placeholders are present", () => {
    const field = {
        default: "",
        default_config: {
            source_type: "context",
            context_path: "legacy.code",
            fallback_value: "legacy-fallback",
        },
        default_source_config: {
            mode: "fixed",
            fallback_value: "new-fixed-fallback",
        },
    };

    const ui = normalizeDefaultSourceUi(field, field.default);
    assert.equal(ui.mode, "fixed");
    assert.equal(ui.fallback_value, "");
    assert.deepEqual(ui.legacy_config, {
        source_type: "context",
        value: "",
        context_path: "legacy.code",
        enum_code: "",
        db_source_code: "",
        fallback_value: "legacy-fallback",
    });
    assert.deepEqual(buildDefaultSourcePayload({
        default: field.default,
        default_source_ui: ui,
    }), {
        default_config: {
            source_type: "context",
            value: "",
            context_path: "legacy.code",
            enum_code: "",
            db_source_code: "",
            fallback_value: "legacy-fallback",
        },
    });
});

test("legacy options config stays hidden from the main UI but remains available for compatibility payloads", () => {
    const field = {
        options_config: {
            source_type: "context",
            context_path: "legacy.options",
            fallback_to_manual: false,
        },
    };

    const ui = normalizeOptionsSourceUi(field);
    assert.equal(ui.mode, "manual");
    assert.deepEqual(buildOptionsSourcePayload({
        options_source_ui: ui,
    }), {
        options_config: {
            source_type: "context",
            context_path: "legacy.options",
            enum_code: "",
            db_source_code: "",
            label_key: "label",
            value_key: "value",
            fallback_to_manual: false,
        },
    });
});

test("legacy options config wins when non-datasource new mode placeholders are present", () => {
    const field = {
        options_config: {
            source_type: "context",
            context_path: "legacy.options",
            fallback_to_manual: false,
        },
        options_source_config: {
            mode: "manual",
            fallback_to_manual: true,
        },
    };

    const ui = normalizeOptionsSourceUi(field);
    assert.equal(ui.mode, "manual");
    assert.equal(ui.fallback_to_manual, true);
    assert.deepEqual(ui.legacy_config, {
        source_type: "context",
        context_path: "legacy.options",
        enum_code: "",
        db_source_code: "",
        label_key: "label",
        value_key: "value",
        fallback_to_manual: false,
    });
    assert.deepEqual(buildOptionsSourcePayload({
        options_source_ui: ui,
    }), {
        options_config: {
            source_type: "context",
            context_path: "legacy.options",
            enum_code: "",
            db_source_code: "",
            label_key: "label",
            value_key: "value",
            fallback_to_manual: false,
        },
    });
});

test("preserves legacy context binding fields while normalizing standard keys", () => {
    const field = {
        context_binding: {
            read_path: "form.NODE_A.code",
            write_path: "form.NODE_A.code",
            write_mode: "merge_if_absent",
            sync_when: "submit",
            alias: "legacy-code",
        },
    };

    const ui = normalizeContextBindingUi(field);
    assert.deepEqual(ui, {
        write_target: "node",
        write_mode: "merge_if_absent",
        legacy_config: {
            sync_when: "submit",
            alias: "legacy-code",
        },
    });
    assert.deepEqual(buildContextBindingPayload({ context_binding: ui }), {
        context_binding: {
            sync_when: "submit",
            alias: "legacy-code",
            write_mode: "merge_if_absent",
        },
    });
});

test("builds context binding payload with only legacy extras when standard keys are empty", () => {
    assert.deepEqual(
        buildContextBindingPayload({
            context_binding: {
                write_target: "none",
                write_mode: "overwrite",
                legacy_config: {
                    sync_when: "submit",
                },
            },
        }),
        {
            context_binding: {
                sync_when: "submit",
                write_target: "none",
            },
        },
    );
});

test("builds context binding payload with explicit write target choices", () => {
    assert.deepEqual(
        buildContextBindingPayload({
            context_binding: {
                write_target: "both",
                write_mode: "merge_if_absent",
                legacy_config: null,
            },
        }),
        {
            context_binding: {
                write_target: "both",
                write_mode: "merge_if_absent",
            },
        },
    );
    assert.deepEqual(
        buildContextBindingPayload({
            context_binding: {
                write_target: "none",
                write_mode: "merge_if_absent",
                legacy_config: null,
            },
        }),
        {
            context_binding: {
                write_target: "none",
            },
        },
    );
});

test("filters metadata by target and component and preserves source params without datasource schema", () => {
    const defaultSources = getAvailableFieldDataSources(metadata, "default", "input");
    const optionSources = getAvailableFieldDataSources(metadata, "options", "select");
    const textSources = getAvailableFieldDataSources(metadata, "default", "paragraph");

    assert.deepEqual(defaultSources.map((item) => item.key), ["ctx_text"]);
    assert.deepEqual(optionSources.map((item) => item.key), ["site_address_select"]);
    assert.deepEqual(textSources.map((item) => item.key), ["ctx_text"]);
    assert.deepEqual(getFieldSourceParamSchema(metadata, "site_address_select", "options"), []);
    assert.deepEqual(
        syncFieldSourceParamsBySchema(metadata, "site_address_select", "options", {
            order_id_path: "runtime.order_id",
            ignored: "x",
        }),
        { order_id_path: "runtime.order_id", ignored: "x" },
    );
});

test("normalizes new metadata and legacy metadata into supported methods", () => {
    const typedMetadata = normalizeFieldDataSourceMetadata([
        {
            key: "typed_default",
            label: "Typed Default",
            data_type: "text",
            support_components: ["input"],
            supported_methods: ["get_default_text"],
        },
        {
            key: "legacy_default",
            label: "Legacy Default",
            data_type: "text",
            support_components: ["input"],
            support_default: true,
        },
    ]);

    assert.deepEqual(typedMetadata[0].supported_methods, ["get_default_text"]);
    assert.deepEqual(typedMetadata[1].supported_methods, ["get_default_text"]);
});

test("builds payloads with new config without re-writing legacy config", () => {
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
    });
    assert.deepEqual(optionsPayload, {
        options_source_config: {
            mode: "data_source",
            source_key: "site_address_select",
            source_params: { order_id_path: "runtime.order_id" },
            fallback_to_manual: false,
        },
    });
});

test("builds payloads without legacy config for new-only datasource interaction", () => {
    const defaultPayload = buildDefaultSourcePayload({
        default: "",
        default_source_ui: {
            mode: "data_source",
            source_key: "ctx_text",
            source_params: { context_path: "form.code" },
            fallback_value: "fallback",
            legacy_config: null,
        },
    });
    const optionsPayload = buildOptionsSourcePayload({
        options_source_ui: {
            mode: "data_source",
            source_key: "site_address_select",
            source_params: { order_id_path: "runtime.order_id" },
            fallback_to_manual: false,
            legacy_config: null,
        },
    });

    assert.deepEqual(defaultPayload, {
        default_source_config: {
            mode: "data_source",
            source_key: "ctx_text",
            source_params: { context_path: "form.code" },
            fallback_value: "fallback",
        },
    });
    assert.deepEqual(optionsPayload, {
        options_source_config: {
            mode: "data_source",
            source_key: "site_address_select",
            source_params: { order_id_path: "runtime.order_id" },
            fallback_to_manual: false,
        },
    });
});
