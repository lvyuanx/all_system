import test from "node:test";
import assert from "node:assert/strict";

import { mountFlowDesigner } from "../oss/static/flow_engine/js/flow_designer.js";
import {
    APPROVAL_MODE_OPTIONS,
    buildFieldDataSourcePlaceholder,
    FORM_REF_CODE_KEY,
    FORM_REF_NAME_KEY,
    NODE_TYPE_OPTIONS,
    RULE_TYPE_OPTIONS,
} from "../oss/static/flow_engine/js/flow_designer_constants.js";

test("flow designer facade re-exports mount function", () => {
    assert.equal(typeof mountFlowDesigner, "function");
});

test("flow designer constants preserve option labels and keys", () => {
    assert.equal(NODE_TYPE_OPTIONS[0].value, "start");
    assert.equal(APPROVAL_MODE_OPTIONS[1].value, "all");
    assert.equal(RULE_TYPE_OPTIONS[0].value, "perm_pack");
    assert.equal(FORM_REF_CODE_KEY, "__form_ref_code");
    assert.equal(FORM_REF_NAME_KEY, "__form_ref_name");
});

test("flow designer field data source placeholder text stays stable", () => {
    assert.equal(buildFieldDataSourcePlaceholder("default"), "请选择默认值数据源");
    assert.equal(buildFieldDataSourcePlaceholder("options"), "请选择选项数据源");
});
