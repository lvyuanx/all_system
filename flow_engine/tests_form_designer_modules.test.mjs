import test from "node:test";
import assert from "node:assert/strict";

import {
    buildFieldDataSourcePlaceholder,
    COMPONENT_ALIAS_MAP,
    COMPONENT_GROUPS,
    COMPONENT_LABEL_MAP,
} from "../oss/static/flow_engine/js/form_designer_constants.js";
import { mountFlowFormDesigner } from "../oss/static/flow_engine/js/form_designer.js";
import {
    buildTextDisplayStyle,
    containerStyle,
} from "../oss/static/flow_engine/js/form_designer_style.js";

test("form designer facade re-exports mount function", () => {
    assert.equal(typeof mountFlowFormDesigner, "function");
});

test("component constants preserve palette shape and aliases", () => {
    assert.equal(Array.isArray(COMPONENT_GROUPS), true);
    assert.equal(COMPONENT_GROUPS.length >= 4, true);
    assert.equal(COMPONENT_LABEL_MAP.input, "单行输入");
    assert.equal(COMPONENT_ALIAS_MAP.signature_pad, "signature");
});

test("field data source placeholder text stays stable", () => {
    assert.equal(buildFieldDataSourcePlaceholder("default"), "请选择默认值数据源");
    assert.equal(buildFieldDataSourcePlaceholder("options"), "请选择选项数据源");
});

test("containerStyle builds grid layout and appends custom css", () => {
    const style = containerStyle({
        component: "container",
        padding: 12,
        gap: 8,
        grid_columns: 3,
        css_text: "background:#fff",
    });
    assert.match(style, /padding:12px/);
    assert.match(style, /gap:8px/);
    assert.match(style, /grid-template-columns:repeat\(3, minmax\(0, 1fr\)\)/);
    assert.match(style, /background:#fff/);
});

test("buildTextDisplayStyle keeps alignment defaults and custom css", () => {
    const style = buildTextDisplayStyle({
        text_align: "center",
        text_v_align: "middle",
        text_min_height: 80,
        css_text: "color:#333",
    });
    assert.match(style, /justify-content:center/);
    assert.match(style, /align-items:center/);
    assert.match(style, /min-height:80px/);
    assert.match(style, /color:#333/);
});
