export const NODE_TYPE_OPTIONS = [
    { label: "开始", value: "start" },
    { label: "任务", value: "task" },
    { label: "条件", value: "condition" },
    { label: "结束", value: "end" },
];

export const APPROVAL_MODE_OPTIONS = [
    { label: "任意满足", value: "any" },
    { label: "全部满足", value: "all" },
];

export const RULE_TYPE_OPTIONS = [
    { label: "权限包", value: "perm_pack" },
    { label: "指定人", value: "user" },
];

export const FORM_REF_CODE_KEY = "__form_ref_code";
export const FORM_REF_NAME_KEY = "__form_ref_name";

export const buildFieldDataSourcePlaceholder = (target) => target === "default"
    ? "请选择默认值数据源"
    : "请选择选项数据源";
