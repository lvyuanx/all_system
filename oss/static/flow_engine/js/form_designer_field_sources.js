export function createFieldDataSourceManager(options = {}) {
    const reactive = options.reactive;
    const activeForm = options.activeForm || (() => null);
    const findNodeLocation = options.findNodeLocation || (() => null);
    const helper = options.fieldSourceHelper || {};
    const {
        getAvailableFieldDataSources,
        getFieldDataSourceByKey,
        getFieldSourceMethodName,
        getFieldSourceParamSchema,
        normalizeFieldDataSourceMetadata,
        syncFieldSourceParamsBySchema,
    } = helper;

    const state = reactive({
        metadata: normalizeFieldDataSourceMetadata(options.initialMetadata || []),
    });

    const fieldDataSourcePicker = reactive({
        visible: false,
        keyword: "",
        target: "default",
        nodeId: "",
        nodeRef: null,
        title: "选择数据源类",
        selectedKey: "",
        page: 1,
        pageSize: 8,
        options: [],
    });

    const getDefaultFieldDataSources = (node) => getAvailableFieldDataSources(state.metadata, "default", node?.component);
    const getOptionsFieldDataSources = (node) => getAvailableFieldDataSources(state.metadata, "options", node?.component);
    const hasCompatibleFieldDataSources = (node, target) => (target === "default" ? getDefaultFieldDataSources(node) : getOptionsFieldDataSources(node)).length > 0;

    const isDualSupportDataSource = (sourceKey, component) => {
        if (!sourceKey) return false;
        const source = getFieldDataSourceByKey(state.metadata, sourceKey);
        const defaultMethod = getFieldSourceMethodName?.("default", component);
        const optionsMethod = getFieldSourceMethodName?.("options", component);
        const supportedMethods = Array.isArray(source?.supported_methods) ? source.supported_methods : [];
        return !!source && !!defaultMethod && !!optionsMethod
            && supportedMethods.includes(defaultMethod)
            && supportedMethods.includes(optionsMethod);
    };

    const refreshFieldDataSourceMetadata = (items) => {
        state.metadata = normalizeFieldDataSourceMetadata(items || []);
    };

    const fetchFieldDataSourceMetadata = async () => {
        if (state.metadata?.length) return;
        try {
            const res = await fetch("/flow_engine/field_data_sources/metadata/", {
                method: "GET",
                credentials: "same-origin",
                headers: { "Accept": "application/json" },
            });
            if (!res.ok) throw new Error(`status ${res.status}`);
            const data = await res.json();
            refreshFieldDataSourceMetadata(data?.items || data || []);
        } catch (err) {
            console.error("加载字段数据源元信息失败", err);
        }
    };

    const getSourceParamsSchema = (node, target) => {
        const ui = target === "default" ? node?.default_source_ui : node?.options_source_ui;
        return getFieldSourceParamSchema(state.metadata, ui?.source_key, target);
    };

    const onFieldDataSourceChange = (node, target) => {
        const ui = target === "default" ? node?.default_source_ui : node?.options_source_ui;
        if (!ui) return;
        ui.source_params = syncFieldSourceParamsBySchema(state.metadata, ui.source_key, target, ui.source_params);
    };

    const getFieldDataSourcePickerNode = () => {
        if (fieldDataSourcePicker.nodeRef && typeof fieldDataSourcePicker.nodeRef === "object") {
            return fieldDataSourcePicker.nodeRef;
        }
        const form = activeForm();
        if (!form || !fieldDataSourcePicker.nodeId) return null;
        return findNodeLocation(form, fieldDataSourcePicker.nodeId)?.node || null;
    };

    const getFieldDataSourceKeyLabel = (key, target, node) => {
        const cleanKey = String(key || "").trim().toLowerCase();
        if (!cleanKey) return "";
        const list = target === "default" ? getDefaultFieldDataSources(node) : getOptionsFieldDataSources(node);
        const item = list.find((source) => source.key === cleanKey);
        return item ? `${item.label} (${item.key})` : cleanKey;
    };

    const getCurrentFieldDataSourceOptions = () => {
        const list = Array.isArray(fieldDataSourcePicker.options) ? fieldDataSourcePicker.options : [];
        const keyword = fieldDataSourcePicker.keyword.trim().toLowerCase();
        if (!keyword) return list;
        return list.filter((item) =>
            item.key.toLowerCase().includes(keyword)
            || (item.label || "").toLowerCase().includes(keyword)
            || (item.data_type || "").toLowerCase().includes(keyword)
        );
    };

    const getCurrentFieldDataSourcePagedOptions = () => {
        const list = getCurrentFieldDataSourceOptions();
        const start = (Math.max(fieldDataSourcePicker.page, 1) - 1) * fieldDataSourcePicker.pageSize;
        return list.slice(start, start + fieldDataSourcePicker.pageSize);
    };

    const openFieldDataSourcePicker = async (node, target) => {
        if (!node) return;
        await fetchFieldDataSourceMetadata();
        fieldDataSourcePicker.visible = true;
        fieldDataSourcePicker.keyword = "";
        fieldDataSourcePicker.target = target;
        fieldDataSourcePicker.nodeId = node.id || "";
        fieldDataSourcePicker.nodeRef = node;
        fieldDataSourcePicker.options = target === "default" ? getDefaultFieldDataSources(node) : getOptionsFieldDataSources(node);
        fieldDataSourcePicker.selectedKey = String((target === "default" ? node?.default_source_ui?.source_key : node?.options_source_ui?.source_key) || "").trim().toLowerCase();
        fieldDataSourcePicker.page = 1;
        fieldDataSourcePicker.title = target === "default" ? "选择默认值数据源类" : "选择选项数据源类";
    };

    const closeFieldDataSourcePicker = () => {
        fieldDataSourcePicker.visible = false;
        fieldDataSourcePicker.keyword = "";
        fieldDataSourcePicker.nodeId = "";
        fieldDataSourcePicker.nodeRef = null;
        fieldDataSourcePicker.selectedKey = "";
        fieldDataSourcePicker.page = 1;
        fieldDataSourcePicker.options = [];
    };

    const chooseFieldDataSource = (item) => {
        if (!item) return;
        fieldDataSourcePicker.selectedKey = item.key;
    };

    const applyFieldDataSourceSelection = () => {
        const node = getFieldDataSourcePickerNode();
        if (!node) return;
        const target = fieldDataSourcePicker.target;
        const ui = target === "default" ? node.default_source_ui : node.options_source_ui;
        if (!ui) return;
        const selectedKey = String(fieldDataSourcePicker.selectedKey || "").trim().toLowerCase();
        const previousKey = ui.source_key;
        ui.source_key = selectedKey;
        onFieldDataSourceChange(node, target);
        if (selectedKey && isDualSupportDataSource(selectedKey, node.component)) {
            const otherTarget = target === "default" ? "options" : "default";
            const otherUi = target === "default" ? node.options_source_ui : node.default_source_ui;
            if (otherUi) {
                otherUi.mode = "data_source";
                otherUi.source_key = selectedKey;
                onFieldDataSourceChange(node, otherTarget);
            }
        } else if (!selectedKey && previousKey && isDualSupportDataSource(previousKey, node.component)) {
            const otherTarget = target === "default" ? "options" : "default";
            const otherUi = target === "default" ? node.options_source_ui : node.default_source_ui;
            if (otherUi && otherUi.source_key === previousKey) {
                otherUi.source_key = "";
                otherUi.mode = otherTarget === "default" ? "fixed" : "manual";
                onFieldDataSourceChange(node, otherTarget);
            }
        }
        closeFieldDataSourcePicker();
    };

    const clearFieldDataSourceSelection = () => {
        fieldDataSourcePicker.selectedKey = "";
    };

    const clearFieldDataSource = (node, target) => {
        if (!node) return;
        const ui = target === "default" ? node.default_source_ui : node.options_source_ui;
        if (!ui) return;
        const previousKey = ui.source_key;
        ui.source_key = "";
        onFieldDataSourceChange(node, target);
        if (previousKey && isDualSupportDataSource(previousKey, node.component)) {
            const otherTarget = target === "default" ? "options" : "default";
            const otherUi = target === "default" ? node.options_source_ui : node.default_source_ui;
            if (otherUi && otherUi.source_key === previousKey) {
                otherUi.source_key = "";
                otherUi.mode = otherTarget === "default" ? "fixed" : "manual";
                onFieldDataSourceChange(node, otherTarget);
            }
        }
    };

    const onFieldDataSourcePickerKeywordChange = () => {
        fieldDataSourcePicker.page = 1;
    };

    return {
        fieldDataSourceMetadataState: state,
        fieldDataSourcePicker,
        refreshFieldDataSourceMetadata,
        fetchFieldDataSourceMetadata,
        getDefaultFieldDataSources,
        getOptionsFieldDataSources,
        hasCompatibleFieldDataSources,
        getSourceParamsSchema,
        onFieldDataSourceChange,
        getFieldDataSourceKeyLabel,
        getCurrentFieldDataSourceOptions,
        getCurrentFieldDataSourcePagedOptions,
        openFieldDataSourcePicker,
        closeFieldDataSourcePicker,
        chooseFieldDataSource,
        applyFieldDataSourceSelection,
        clearFieldDataSourceSelection,
        clearFieldDataSource,
        onFieldDataSourcePickerKeywordChange,
    };
}
