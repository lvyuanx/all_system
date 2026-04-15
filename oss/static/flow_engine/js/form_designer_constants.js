export const HISTORY_LIMIT = 80;
export const DRAFT_STORAGE_PREFIX = "flow_form_designer_draft";

export const PLACEHOLDER_COMPONENTS = new Set(["placeholder"]);
export const TEXT_COMPONENTS = new Set(["title_h1", "title_h2", "title_h3", "title_h4", "title_h5", "paragraph"]);
export const STRUCTURE_DISPLAY_COMPONENTS = new Set(["divider", "spacer", "section_header", "card_block"]);
export const SOURCE_AWARE_DISPLAY_COMPONENTS = new Set(["section_header", "card_block"]);
export const VARIABLE_COMPONENTS = new Set(["var_username", "var_phone", "var_full_name"]);
export const DISPLAY_COMPONENTS = new Set([
    ...PLACEHOLDER_COMPONENTS,
    ...TEXT_COMPONENTS,
    ...STRUCTURE_DISPLAY_COMPONENTS,
    ...VARIABLE_COMPONENTS,
]);

export const VARIABLE_META_MAP = {
    var_username: {
        key: "username",
        label: "用户名",
    },
    var_phone: {
        key: "phone",
        label: "手机号",
    },
    var_full_name: {
        key: "full_name",
        label: "姓名",
    },
};

export const COMPONENT_GROUPS = [
    {
        key: "input",
        title: "输入类组件",
        list: [
            { value: "input", label: "单行输入", thumb: "Aa" },
            { value: "textarea", label: "多行文本", thumb: "TXT" },
            { value: "number", label: "数字", thumb: "123" },
            { value: "file", label: "文件上传", thumb: "FILE" },
            { value: "signature", label: "手写签名", thumb: "签" },
        ],
    },
    {
        key: "select",
        title: "选择类组件",
        list: [
            { value: "select", label: "下拉选择", thumb: "SEL" },
            { value: "radio", label: "单选", thumb: "RAD" },
            { value: "checkbox", label: "多选", thumb: "CHK" },
            { value: "switch", label: "开关", thumb: "ON" },
            { value: "date", label: "日期", thumb: "D" },
            { value: "datetime", label: "日期时间", thumb: "DT" },
        ],
    },
    {
        key: "layout",
        title: "布局类组件",
        list: [
            { value: "container", label: "容器", thumb: "GRID" },
            { value: "card_block", label: "信息卡片", thumb: "CARD" },
            { value: "divider", label: "分割线", thumb: "---" },
            { value: "spacer", label: "间距块", thumb: "SPC" },
            { value: "placeholder", label: "占位符", thumb: "___" },
        ],
    },
    {
        key: "text",
        title: "文本组件",
        list: [
            { value: "section_header", label: "区块标题", thumb: "SEC" },
            { value: "title_h1", label: "一级标题", thumb: "H1" },
            { value: "title_h2", label: "二级标题", thumb: "H2" },
            { value: "title_h3", label: "三级标题", thumb: "H3" },
            { value: "title_h4", label: "四级标题", thumb: "H4" },
            { value: "title_h5", label: "五级标题", thumb: "H5" },
            { value: "paragraph", label: "文本", thumb: "TXT" },
        ],
    },
];

export const COMPONENT_ALIAS_MAP = {
    text: "input",
    string: "input",
    upload: "file",
    choice: "select",
    enum: "select",
    bool: "switch",
    boolean: "switch",
    int: "number",
    integer: "number",
    float: "number",
    decimal: "number",
    sign: "signature",
    signpad: "signature",
    signature_pad: "signature",
    hr: "divider",
    line: "divider",
    divider_line: "divider",
    space: "spacer",
    blank: "spacer",
    sectiontitle: "section_header",
    section_title: "section_header",
    info_card: "card_block",
    display_card: "card_block",
};

export const COMPONENT_PALETTE = COMPONENT_GROUPS.flatMap((group) => group.list);
export const COMPONENT_VALUE_SET = new Set(COMPONENT_PALETTE.map((item) => item.value));
export const COMPONENT_LABEL_MAP = COMPONENT_PALETTE.reduce((acc, item) => {
    acc[item.value] = item.label;
    return acc;
}, {});

export const PALETTE_TAB_SET = new Set(["all", "input", "select", "layout"]);

export const buildFieldDataSourcePlaceholder = (target) => target === "default"
    ? "请选择默认值数据源"
    : "请选择选项数据源";
