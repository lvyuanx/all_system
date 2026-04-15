import {
    buildFieldDataSourcePlaceholder,
    COMPONENT_GROUPS,
    COMPONENT_ALIAS_MAP,
    COMPONENT_LABEL_MAP,
    COMPONENT_VALUE_SET,
    DISPLAY_COMPONENTS,
    DRAFT_STORAGE_PREFIX,
    HISTORY_LIMIT,
    PLACEHOLDER_COMPONENTS,
    SOURCE_AWARE_DISPLAY_COMPONENTS,
    STRUCTURE_DISPLAY_COMPONENTS,
    TEXT_COMPONENTS,
    VARIABLE_COMPONENTS,
    VARIABLE_META_MAP,
} from "./form_designer_constants.js";
import { createComponentPreview } from "./form_designer_component_preview.js";
import { createDesignerNodeItem } from "./form_designer_designer_node_item.js";
import { createFieldDataSourceManager } from "./form_designer_field_sources.js";
import { createPreviewFieldRender } from "./form_designer_preview_field_render.js";

export function mountFlowFormDesigner(options = {}) {
    const { reactive, ref, computed, onMounted, onBeforeUnmount, inject, watch } = Vue;

    const flowId = Number(options.flowId || 0);
    const queryParams = new URLSearchParams(window.location.search || "");
    const shouldCreateFormFromQuery = queryParams.get("new_form") === "1";
    const initialGroupName = String(queryParams.get("group_name") || "").trim();
    const selectedFormCodeFromQuery = String(queryParams.get("selected_code") || "").trim();
    const previousUrl = options.previousUrl || "";
    const currentUser = options.currentUser || {};
    const {
        buildContextBindingPayload,
        buildDefaultSourcePayload,
        buildOptionsSourcePayload,
        getAvailableFieldDataSources,
        getFieldDataSourceByKey,
        getFieldSourceMethodName,
        getFieldSourceParamSchema,
        normalizeContextBindingUi,
        normalizeDefaultSourceUi,
        normalizeFieldDataSourceMetadata,
        normalizeOptionsSourceUi,
        shouldUseManualOptions,
        syncFieldSourceParamsBySchema,
    } = options.fieldSourceHelper || {};
    let fieldDataSourceMetadata = normalizeFieldDataSourceMetadata(options.fieldDataSourceMetadata || []);

    const resolveVariableValueByKey = (key) => {
        const cleanKey = String(key || "").trim();
        if (!cleanKey) return "";
        return currentUser?.[cleanKey] ?? "";
    };

    const ComponentPreview = createComponentPreview(resolveVariableValueByKey);
    const DesignerNodeItem = createDesignerNodeItem(ComponentPreview);
    const {
        PreviewFieldRender,
        SignatureField,
    } = createPreviewFieldRender(resolveVariableValueByKey);

    window.createApp({
        delimiters: ["[[", "]]"],
        components: {
            ComponentPreview,
            DesignerNodeItem,
            PreviewFieldRender,
            SignatureField,
        },
        setup() {
            const ElMessage = inject("ElMessage");
            const ElMessageBox = inject("ElMessageBox");

            const pageData = reactive({
                pageLoading: true,
                saving: false,
                sourceLoading: false,
            });

            const previewDialog = reactive({
                visible: false,
                nodes: [],
                formData: {},
                rules: {},
                submittedJson: "",
                sourceNodes: [],
                contextText: "",
            });
            const previewFormRef = ref(null);

            const jsonDialog = reactive({
                visible: false,
                content: "",
            });

            const componentGroups = COMPONENT_GROUPS;
            const componentValueSet = COMPONENT_VALUE_SET;
            const componentLabelMap = COMPONENT_LABEL_MAP;
            const componentAliasMap = COMPONENT_ALIAS_MAP;

            const forms = reactive([]);
            const selectedFormIndex = ref(-1);
            const selectedFormIndexValue = ref("");
            const selectedNodeId = ref("");
            const activeRightTab = ref("field");
            const paletteState = reactive({
                tab: "all",
                keyword: "",
            });
            const paletteTabSet = new Set(["all", "input", "select", "layout"]);

            const filteredComponentGroups = computed(() => {
                const keyword = String(paletteState.keyword || "").trim().toLowerCase();
                const activeTab = paletteTabSet.has(paletteState.tab) ? paletteState.tab : "all";
                const groups = componentGroups.filter((group) => {
                    if (activeTab === "all") return true;
                    return group.key === activeTab;
                });
                const filtered = groups
                    .map((group) => {
                        const list = group.list.filter((item) => {
                            if (!keyword) return true;
                            return (
                                String(item.label || "").toLowerCase().includes(keyword)
                                || String(item.value || "").toLowerCase().includes(keyword)
                            );
                        });
                        return {
                            ...group,
                            list,
                        };
                    })
                    .filter((group) => group.list.length);
                if (!filtered.length && !keyword) {
                    return componentGroups;
                }
                return filtered;
            });

            const dragState = reactive({
                mode: "",
                paletteComponent: "",
                sourceNodeId: "",
                overContainerId: "",
                overNodeId: "",
            });

            let idSeed = 1;
            const nextId = (prefix) => {
                const value = `${prefix}_${idSeed}`;
                idSeed += 1;
                return value;
            };

            const deepClone = (obj) => JSON.parse(JSON.stringify(obj));
            const historyStack = ref([]);
            const historyIndex = ref(-1);
            const isApplyingHistory = ref(false);
            let historyCaptureTimer = null;
            let draftSaveTimer = null;

            const getDraftStorageKey = () => `${DRAFT_STORAGE_PREFIX}_${flowId || "draft"}`;

            const captureStateSnapshot = () => ({
                forms: deepClone(forms),
                selectedFormIndex: selectedFormIndex.value,
                selectedNodeId: selectedNodeId.value,
                activeRightTab: activeRightTab.value,
            });

            const getStateSignature = (snapshot) => JSON.stringify(snapshot);

            const setFormsFromRaw = (rawForms, activeIndex = 0) => {
                const normalized = (Array.isArray(rawForms) ? rawForms : [])
                    .map((raw, index) => normalizeForm(raw, index))
                    .filter(Boolean)
                    .sort((a, b) => (a.order || 0) - (b.order || 0));
                forms.splice(0, forms.length, ...normalized);
                if (forms.length) {
                    const safeIndex = Number.isInteger(activeIndex) ? activeIndex : 0;
                    setActiveForm(Math.min(Math.max(safeIndex, 0), forms.length - 1));
                } else {
                    setActiveForm(-1);
                }
            };

            const restoreStateSnapshot = (snapshot) => {
                if (!snapshot || typeof snapshot !== "object") return;
                isApplyingHistory.value = true;
                try {
                    setFormsFromRaw(snapshot.forms || [], snapshot.selectedFormIndex ?? 0);
                    const form = activeForm.value;
                    if (form && snapshot.selectedNodeId) {
                        const exists = findNodeLocation(form, snapshot.selectedNodeId);
                        selectedNodeId.value = exists ? snapshot.selectedNodeId : "";
                    } else {
                        selectedNodeId.value = "";
                    }
                    activeRightTab.value = snapshot.activeRightTab || "field";
                } finally {
                    isApplyingHistory.value = false;
                }
            };

            const resetHistory = () => {
                historyStack.value = [];
                historyIndex.value = -1;
            };

            const pushHistorySnapshot = () => {
                if (isApplyingHistory.value) return;
                const snapshot = captureStateSnapshot();
                const signature = getStateSignature(snapshot);
                const current = historyStack.value[historyIndex.value];
                if (current && current.signature === signature) return;
                if (historyIndex.value < historyStack.value.length - 1) {
                    historyStack.value.splice(historyIndex.value + 1);
                }
                historyStack.value.push({
                    signature,
                    snapshot,
                });
                if (historyStack.value.length > HISTORY_LIMIT) {
                    historyStack.value.shift();
                }
                historyIndex.value = historyStack.value.length - 1;
            };

            const canUndo = computed(() => historyIndex.value > 0);
            const canRedo = computed(() => historyIndex.value >= 0 && historyIndex.value < historyStack.value.length - 1);

            const undo = () => {
                if (!canUndo.value) return;
                historyIndex.value -= 1;
                const item = historyStack.value[historyIndex.value];
                if (item) {
                    restoreStateSnapshot(item.snapshot);
                }
            };

            const redo = () => {
                if (!canRedo.value) return;
                historyIndex.value += 1;
                const item = historyStack.value[historyIndex.value];
                if (item) {
                    restoreStateSnapshot(item.snapshot);
                }
            };

            const saveDraftToLocal = () => {
                if (isApplyingHistory.value || pageData.pageLoading) return;
                const payload = {
                    forms: buildPayloadForms(),
                };
                localStorage.setItem(getDraftStorageKey(), JSON.stringify({
                    updated_at: Date.now(),
                    payload,
                }));
            };

            const clearDraft = () => {
                localStorage.removeItem(getDraftStorageKey());
            };

            const scheduleAutoCapture = () => {
                if (isApplyingHistory.value || pageData.pageLoading) return;
                if (historyCaptureTimer) clearTimeout(historyCaptureTimer);
                historyCaptureTimer = setTimeout(() => {
                    pushHistorySnapshot();
                }, 280);
                if (draftSaveTimer) clearTimeout(draftSaveTimer);
                draftSaveTimer = setTimeout(() => {
                    saveDraftToLocal();
                }, 360);
            };

            const createOption = () => ({
                id: nextId("option"),
                label: "",
                value: "",
            });

            let getDefaultFieldDataSources;
            let getOptionsFieldDataSources;
            let hasCompatibleFieldDataSources;
            let getSourceParamsSchema;
            let onFieldDataSourceChange;
            let getFieldDataSourceKeyLabel;
            let getCurrentFieldDataSourceOptions;
            let getCurrentFieldDataSourcePagedOptions;
            let fieldDataSourcePicker;
            let fetchFieldDataSourceMetadata;
            let openFieldDataSourcePicker;
            let closeFieldDataSourcePicker;
            let chooseFieldDataSource;
            let applyFieldDataSourceSelection;
            let clearFieldDataSourceSelection;
            let clearFieldDataSource;
            let onFieldDataSourcePickerKeywordChange;

            const usesManualOptions = (node) => shouldUseManualOptions(node);

            const createNode = (component = "input") => {
                if (component === "container") {
                    return {
                        id: nextId("node"),
                        component: "container",
                        label: "容器",
                        css_text: "",
                        js_text: "",
                        layout_mode: "grid",
                        grid_columns: 2,
                        gap: 12,
                        padding: 10,
                        children: [],
                    };
                }

                if (PLACEHOLDER_COMPONENTS.has(component)) {
                    return {
                        id: nextId("node"),
                        component: "placeholder",
                        label: "占位符",
                        content: "",
                        css_text: "",
                        js_text: "",
                    };
                }

                if (component === "divider") {
                    return {
                        id: nextId("node"),
                        component: "divider",
                        label: componentLabelMap[component] || "分割线",
                        line_style: "solid",
                        line_color: "#d7deea",
                        line_thickness: 1,
                        line_margin: 12,
                        css_text: "",
                        js_text: "",
                    };
                }

                if (component === "spacer") {
                    return {
                        id: nextId("node"),
                        component: "spacer",
                        label: componentLabelMap[component] || "间距块",
                        height: 24,
                        css_text: "",
                        js_text: "",
                    };
                }

                if (component === "section_header") {
                    const content = componentLabelMap[component] || "区块标题";
                    return {
                        id: nextId("node"),
                        component,
                        label: componentLabelMap[component] || "区块标题",
                        content,
                        sub_content: "",
                        default_source_ui: normalizeDefaultSourceUi({}, content),
                        css_text: "",
                        js_text: "",
                    };
                }

                if (component === "card_block") {
                    const content = "请填写说明内容";
                    return {
                        id: nextId("node"),
                        component,
                        label: componentLabelMap[component] || "信息卡片",
                        title: "信息卡片",
                        content,
                        card_padding: 12,
                        card_radius: 10,
                        card_shadow: false,
                        default_source_ui: normalizeDefaultSourceUi({}, content),
                        css_text: "",
                        js_text: "",
                    };
                }

                if (TEXT_COMPONENTS.has(component)) {
                    return {
                        id: nextId("node"),
                        component,
                        label: componentLabelMap[component] || "文本",
                        content: componentLabelMap[component] || "文本",
                        text_align: "left",
                        text_v_align: "top",
                        text_min_height: 48,
                        default_source_ui: {
                            mode: "fixed",
                            source_key: "",
                            source_params: {},
                            fallback_value: "",
                            legacy_config: null,
                        },
                        css_text: "",
                        js_text: "",
                    };
                }

                if (VARIABLE_COMPONENTS.has(component)) {
                    const variableMeta = VARIABLE_META_MAP[component] || { key: "", label: "变量" };
                    return {
                        id: nextId("node"),
                        component,
                        label: componentLabelMap[component] || variableMeta.label,
                        variable_key: variableMeta.key,
                        variable_label: variableMeta.label,
                        css_text: "",
                        js_text: "",
                    };
                }

                const node = {
                    id: nextId("node"),
                    component,
                    key: "",
                    label: componentLabelMap[component] || "新组件",
                    disabled: false,
                    required: false,
                    placeholder: "",
                    default: "",
                    css_text: "",
                    js_text: "",
                    rows: component === "textarea" ? 3 : undefined,
                    min: undefined,
                    max: undefined,
                    step: component === "number" ? 1 : undefined,
                    accept: component === "file" ? "" : undefined,
                    multiple: component === "file" ? false : undefined,
                    default_source_ui: {
                        mode: "fixed",
                        source_key: "",
                        source_params: {},
                        fallback_value: "",
                        legacy_config: null,
                    },
                context_binding: {
                    write_target: "flow",
                    write_mode: "overwrite",
                },
                    options_source_ui: {
                        mode: "manual",
                        source_key: "",
                        source_params: {},
                        fallback_to_manual: true,
                        legacy_config: null,
                    },
                    options: ["select", "radio", "checkbox"].includes(component) ? [createOption(), createOption()] : [],
                };

                if (component === "switch") {
                    node.default = false;
                } else if (component === "checkbox") {
                    node.default = [];
                }
                node.default_source_ui = normalizeDefaultSourceUi(node, node.default);
                node.options_source_ui = normalizeOptionsSourceUi(node);
                return node;
            };

            const normalizeOption = (option) => {
                if (option && typeof option === "object") {
                    return {
                        id: nextId("option"),
                        label: String(option.label ?? option.name ?? option.value ?? ""),
                        value: option.value ?? option.id ?? option.label ?? option.name ?? "",
                    };
                }
                return {
                    id: nextId("option"),
                    label: String(option ?? ""),
                    value: option ?? "",
                };
            };

            const normalizeDefaultValue = (component, rawNode) => {
                const hasDefault = Object.prototype.hasOwnProperty.call(rawNode || {}, "default");
                if (hasDefault) {
                    return rawNode.default;
                }
                if (Object.prototype.hasOwnProperty.call(rawNode || {}, "default_value")) {
                    return rawNode.default_value;
                }
                if (component === "switch") return false;
                if (component === "checkbox") return [];
                return "";
            };

            const normalizeNode = (rawNode, index = 0) => {
                if (!rawNode || typeof rawNode !== "object") return null;

                let component = String(rawNode.component || rawNode.type || rawNode.widget || "input").toLowerCase();
                component = componentAliasMap[component] || component;
                if (!componentValueSet.has(component) && !VARIABLE_COMPONENTS.has(component)) {
                    component = "input";
                }

                if (component === "container") {
                    const rawChildren = Array.isArray(rawNode.children) ? rawNode.children : [];
                    return {
                        id: nextId("node"),
                        component: "container",
                        label: String(rawNode.label || rawNode.title || `容器${index + 1}`),
                        css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                        js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                        layout_mode: "grid",
                        grid_columns: Number.isFinite(Number(rawNode.grid_columns)) ? Number(rawNode.grid_columns) : 2,
                        gap: Number.isFinite(Number(rawNode.gap)) ? Number(rawNode.gap) : 12,
                        padding: Number.isFinite(Number(rawNode.padding)) ? Number(rawNode.padding) : 10,
                        children: rawChildren
                            .map((child, childIndex) => normalizeNode(child, childIndex))
                            .filter(Boolean),
                    };
                }

                if (PLACEHOLDER_COMPONENTS.has(component)) {
                    return {
                        id: nextId("node"),
                        component: "placeholder",
                        label: String(rawNode.label || componentLabelMap[component] || "占位符"),
                        content: String(rawNode.content || rawNode.text || ""),
                        css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                        js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                    };
                }

                if (component === "divider") {
                    return {
                        id: nextId("node"),
                        component: "divider",
                        label: String(rawNode.label || componentLabelMap[component] || "分割线"),
                        line_style: String(rawNode.line_style || rawNode.style_type || "solid"),
                        line_color: String(rawNode.line_color || rawNode.color || "#d7deea"),
                        line_thickness: Number.isFinite(Number(rawNode.line_thickness))
                            ? Number(rawNode.line_thickness)
                            : 1,
                        line_margin: Number.isFinite(Number(rawNode.line_margin))
                            ? Number(rawNode.line_margin)
                            : 12,
                        css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                        js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                    };
                }

                if (component === "spacer") {
                    return {
                        id: nextId("node"),
                        component: "spacer",
                        label: String(rawNode.label || componentLabelMap[component] || "间距块"),
                        height: Number.isFinite(Number(rawNode.height)) ? Number(rawNode.height) : 24,
                        css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                        js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                    };
                }

                if (component === "section_header") {
                    const content = String(rawNode.content || rawNode.text || rawNode.label || componentLabelMap[component] || "");
                    return {
                        id: nextId("node"),
                        component,
                        label: String(rawNode.label || componentLabelMap[component] || "区块标题"),
                        content,
                        sub_content: String(rawNode.sub_content || rawNode.subTitle || rawNode.subtitle || ""),
                        default_source_ui: normalizeDefaultSourceUi(rawNode, content),
                        css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                        js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                    };
                }

                if (component === "card_block") {
                    const content = String(rawNode.content || rawNode.text || "");
                    return {
                        id: nextId("node"),
                        component,
                        label: String(rawNode.label || componentLabelMap[component] || "信息卡片"),
                        title: String(rawNode.title || rawNode.label || "信息卡片"),
                        content,
                        card_padding: Number.isFinite(Number(rawNode.card_padding))
                            ? Number(rawNode.card_padding)
                            : 12,
                        card_radius: Number.isFinite(Number(rawNode.card_radius))
                            ? Number(rawNode.card_radius)
                            : 10,
                        card_shadow: !!rawNode.card_shadow,
                        default_source_ui: normalizeDefaultSourceUi(rawNode, content),
                        css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                        js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                    };
                }

                if (TEXT_COMPONENTS.has(component)) {
                    return {
                        id: nextId("node"),
                        component,
                        label: String(rawNode.label || rawNode.title || componentLabelMap[component] || `文本${index + 1}`),
                        content: String(rawNode.content || rawNode.text || rawNode.label || componentLabelMap[component] || ""),
                        text_align: String(rawNode.text_align || rawNode.align || "left"),
                        text_v_align: String(rawNode.text_v_align || rawNode.vertical_align || "top"),
                        text_min_height: Number.isFinite(Number(rawNode.text_min_height))
                            ? Number(rawNode.text_min_height)
                            : 48,
                        default_source_ui: normalizeDefaultSourceUi(
                            rawNode,
                            String(rawNode.content || rawNode.text || rawNode.label || componentLabelMap[component] || ""),
                        ),
                        css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                        js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                    };
                }

                if (VARIABLE_COMPONENTS.has(component)) {
                    const variableMeta = VARIABLE_META_MAP[component] || { key: "", label: "变量" };
                    return {
                        id: nextId("node"),
                        component,
                        label: String(rawNode.label || componentLabelMap[component] || variableMeta.label),
                        variable_key: String(rawNode.variable_key || variableMeta.key),
                        variable_label: String(rawNode.variable_label || variableMeta.label),
                        css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                        js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                    };
                }

                const normalized = {
                    id: nextId("node"),
                    component,
                    key: String(rawNode.key || rawNode.name || rawNode.prop || "").trim(),
                    label: String(rawNode.label || rawNode.title || rawNode.name || `字段${index + 1}`),
                    disabled: !!rawNode.disabled,
                    required: !!rawNode.required,
                    placeholder: rawNode.placeholder || "",
                    default: normalizeDefaultValue(component, rawNode),
                    css_text: rawNode.css_text || rawNode.css || rawNode.style || "",
                    js_text: rawNode.js_text || rawNode.js || rawNode.script || "",
                    rows: Number.isFinite(Number(rawNode.rows)) ? Number(rawNode.rows) : 3,
                    min: rawNode.min,
                    max: rawNode.max,
                    step: Number.isFinite(Number(rawNode.step)) ? Number(rawNode.step) : 1,
                    accept: rawNode.accept || "",
                    multiple: !!rawNode.multiple,
                    default_source_ui: normalizeDefaultSourceUi(
                        rawNode,
                        normalizeDefaultValue(component, rawNode),
                    ),
                    context_binding: normalizeContextBindingUi(rawNode),
                    options_source_ui: normalizeOptionsSourceUi(rawNode),
                    options: [],
                };

                if (["select", "radio", "checkbox"].includes(component)) {
                    const rawOptions = rawNode.options || rawNode.choices || rawNode.enum || [];
                    normalized.options = Array.isArray(rawOptions) ? rawOptions.map(normalizeOption) : [];
                    if (!normalized.options.length) {
                        normalized.options = [createOption()];
                    }
                }

                if (component !== "textarea") normalized.rows = undefined;
                if (component !== "number") {
                    normalized.min = undefined;
                    normalized.max = undefined;
                    normalized.step = undefined;
                }
                if (component !== "file") {
                    normalized.accept = undefined;
                    normalized.multiple = undefined;
                }
                return normalized;
            };

            const normalizeForm = (rawForm, index = 0) => {
                if (!rawForm || typeof rawForm !== "object") return null;
                const rawFields = Array.isArray(rawForm.fields) ? rawForm.fields : [];
                return {
                    id: nextId("form"),
                    code: String(rawForm.code || "").trim(),
                    name: String(rawForm.name || "").trim(),
                    group_name: String(rawForm.group_name || rawForm.group || "").trim(),
                    description: String(rawForm.description || "").trim(),
                    order: Number.isFinite(Number(rawForm.order)) ? Number(rawForm.order) : index,
                    nodes: rawFields
                        .map((field, fieldIndex) => normalizeNode(field, fieldIndex))
                        .filter(Boolean),
                };
            };

            const activeForm = computed(() => {
                if (selectedFormIndex.value < 0) return null;
                return forms[selectedFormIndex.value] || null;
            });

            const countNodes = (nodes) =>
                (nodes || []).reduce((sum, node) => {
                    if (!node || typeof node !== "object") return sum;
                    if (node.component === "container") {
                        return sum + 1 + countNodes(node.children || []);
                    }
                    return sum + 1;
                }, 0);

            const activeFormNodeCount = computed(() => countNodes(activeForm.value?.nodes || []));

            const findNodeLocation = (form, nodeId) => {
                if (!form || !nodeId) return null;
                const search = (list, parentNode = null) => {
                    for (let i = 0; i < (list || []).length; i += 1) {
                        const current = list[i];
                        if (!current || typeof current !== "object") continue;
                        if (current.id === nodeId) {
                            return {
                                node: current,
                                parentList: list,
                                index: i,
                                parentNode,
                            };
                        }
                        if (current.component === "container" && Array.isArray(current.children)) {
                            const found = search(current.children, current);
                            if (found) return found;
                        }
                    }
                    return null;
                };
                return search(form.nodes, null);
            };

            const fieldSourceManager = createFieldDataSourceManager({
                reactive,
                activeForm: () => activeForm.value,
                findNodeLocation,
                fieldSourceHelper: options.fieldSourceHelper || {},
                initialMetadata: fieldDataSourceMetadata,
            });
            getDefaultFieldDataSources = fieldSourceManager.getDefaultFieldDataSources;
            getOptionsFieldDataSources = fieldSourceManager.getOptionsFieldDataSources;
            hasCompatibleFieldDataSources = fieldSourceManager.hasCompatibleFieldDataSources;
            getSourceParamsSchema = fieldSourceManager.getSourceParamsSchema;
            onFieldDataSourceChange = fieldSourceManager.onFieldDataSourceChange;
            getFieldDataSourceKeyLabel = fieldSourceManager.getFieldDataSourceKeyLabel;
            getCurrentFieldDataSourceOptions = fieldSourceManager.getCurrentFieldDataSourceOptions;
            getCurrentFieldDataSourcePagedOptions = fieldSourceManager.getCurrentFieldDataSourcePagedOptions;
            fieldDataSourcePicker = fieldSourceManager.fieldDataSourcePicker;
            fetchFieldDataSourceMetadata = fieldSourceManager.fetchFieldDataSourceMetadata;
            openFieldDataSourcePicker = fieldSourceManager.openFieldDataSourcePicker;
            closeFieldDataSourcePicker = fieldSourceManager.closeFieldDataSourcePicker;
            chooseFieldDataSource = fieldSourceManager.chooseFieldDataSource;
            applyFieldDataSourceSelection = fieldSourceManager.applyFieldDataSourceSelection;
            clearFieldDataSourceSelection = fieldSourceManager.clearFieldDataSourceSelection;
            clearFieldDataSource = fieldSourceManager.clearFieldDataSource;
            onFieldDataSourcePickerKeywordChange = fieldSourceManager.onFieldDataSourcePickerKeywordChange;
            fieldDataSourceMetadata = fieldSourceManager.fieldDataSourceMetadataState.metadata;

            const nodeContainsId = (node, targetId) => {
                if (!node || typeof node !== "object" || !targetId) return false;
                if (node.id === targetId) return true;
                if (node.component !== "container" || !Array.isArray(node.children)) return false;
                return node.children.some((child) => nodeContainsId(child, targetId));
            };

            const selectedNode = computed(() => {
                const form = activeForm.value;
                if (!form || !selectedNodeId.value) return null;
                const location = findNodeLocation(form, selectedNodeId.value);
                return location ? location.node : null;
            });

            const previewNodes = computed(() => {
                const dialogNodes = Array.isArray(previewDialog.nodes) ? previewDialog.nodes : [];
                if (dialogNodes.length) return dialogNodes;
                const activeNodes = Array.isArray(activeForm.value?.nodes) ? activeForm.value.nodes : [];
                return activeNodes;
            });

            const previewHasNodes = computed(() => Array.isArray(previewNodes.value) && previewNodes.value.length > 0);

            const setActiveForm = (index) => {
                selectedFormIndex.value = index;
                selectedFormIndexValue.value = index >= 0 ? String(index) : "";
                selectedNodeId.value = "";
            };

            const onSelectFormByValue = (value) => {
                const index = Number(value);
                if (Number.isNaN(index) || index < 0 || index >= forms.length) {
                    setActiveForm(-1);
                    return;
                }
                setActiveForm(index);
            };

            const addForm = () => {
                forms.push({
                    id: nextId("form"),
                    code: "",
                    name: `新表单${forms.length + 1}`,
                    group_name: initialGroupName,
                    description: "",
                    order: forms.length,
                    nodes: [],
                });
                setActiveForm(forms.length - 1);
                activeRightTab.value = "form";
            };

            const removeForm = () => {
                if (selectedFormIndex.value < 0) return;
                forms.splice(selectedFormIndex.value, 1);
                if (!forms.length) {
                    setActiveForm(-1);
                    return;
                }
                setActiveForm(Math.max(0, selectedFormIndex.value - 1));
            };

            const componentLabel = (component) => componentLabelMap[component] || component;

            const clearDragState = () => {
                dragState.mode = "";
                dragState.paletteComponent = "";
                dragState.sourceNodeId = "";
                dragState.overContainerId = "";
                dragState.overNodeId = "";
            };

            const onPaletteDragStart = (component) => {
                dragState.mode = "palette";
                dragState.paletteComponent = component;
                dragState.sourceNodeId = "";
                dragState.overContainerId = "";
                dragState.overNodeId = "";
            };

            const onNodeDragStart = (nodeId) => {
                dragState.mode = "move";
                dragState.sourceNodeId = nodeId;
                dragState.paletteComponent = "";
                dragState.overContainerId = "";
                dragState.overNodeId = "";
            };

            const isDraggingActive = computed(() =>
                dragState.mode === "palette"
                || (dragState.mode === "move" && !!dragState.sourceNodeId));

            const onContainerDragOver = (containerId) => {
                if (!isDraggingActive.value) return;
                dragState.overContainerId = containerId || "";
            };

            const onContainerDragLeave = (event, containerId) => {
                if (dragState.overContainerId !== containerId) return;
                const next = event?.relatedTarget;
                if (next && event?.currentTarget?.contains?.(next)) {
                    return;
                }
                dragState.overContainerId = "";
            };

            const isContainerDropActive = (containerId) =>
                isDraggingActive.value && dragState.overContainerId === containerId;

            const onNodeDragEnter = (nodeId) => {
                if (!isDraggingActive.value) return;
                if (nodeId === dragState.sourceNodeId) return;
                dragState.overNodeId = nodeId || "";
            };

            const isNodeDropTarget = (nodeId) =>
                isDraggingActive.value && dragState.overNodeId === nodeId && nodeId !== dragState.sourceNodeId;

            const selectNode = (nodeId) => {
                selectedNodeId.value = nodeId || "";
                activeRightTab.value = "field";
            };

            const addNodeToForm = (component, targetContainerId = "", beforeNodeId = "") => {
                const form = activeForm.value;
                if (!form) return;
                const node = createNode(component);
                if (targetContainerId) {
                    const containerLoc = findNodeLocation(form, targetContainerId);
                    if (!containerLoc || containerLoc.node.component !== "container") return;
                    if (!Array.isArray(containerLoc.node.children)) {
                        containerLoc.node.children = [];
                    }
                    const list = containerLoc.node.children;
                    if (beforeNodeId) {
                        const targetIndex = list.findIndex((item) => item.id === beforeNodeId);
                        if (targetIndex >= 0) {
                            list.splice(targetIndex, 0, node);
                        } else {
                            list.push(node);
                        }
                    } else {
                        list.push(node);
                    }
                } else if (beforeNodeId) {
                    const targetLoc = findNodeLocation(form, beforeNodeId);
                    if (targetLoc) {
                        targetLoc.parentList.splice(targetLoc.index, 0, node);
                    } else {
                        form.nodes.push(node);
                    }
                } else {
                    form.nodes.push(node);
                }
                selectedNodeId.value = node.id;
            };

            const addComponentByClick = (component) => {
                if (!activeForm.value) {
                    addForm();
                }
                addNodeToForm(component);
            };

            const moveNodeBeforeTarget = (sourceNodeId, targetNodeId) => {
                const form = activeForm.value;
                if (!form || !sourceNodeId || !targetNodeId || sourceNodeId === targetNodeId) return;
                const sourceLoc = findNodeLocation(form, sourceNodeId);
                const targetLoc = findNodeLocation(form, targetNodeId);
                if (!sourceLoc || !targetLoc) return;
                if (nodeContainsId(sourceLoc.node, targetNodeId)) {
                    ElMessage.warning("不能将容器拖放到自身或子容器中");
                    return;
                }

                const node = sourceLoc.node;
                sourceLoc.parentList.splice(sourceLoc.index, 1);

                let targetIndex = targetLoc.index;
                if (sourceLoc.parentList === targetLoc.parentList && sourceLoc.index < targetLoc.index) {
                    targetIndex -= 1;
                }
                targetLoc.parentList.splice(targetIndex, 0, node);
            };

            const moveNodeIntoContainer = (sourceNodeId, containerId) => {
                const form = activeForm.value;
                if (!form || !sourceNodeId || !containerId) return;
                const sourceLoc = findNodeLocation(form, sourceNodeId);
                const containerLoc = findNodeLocation(form, containerId);
                if (!sourceLoc || !containerLoc || containerLoc.node.component !== "container") return;
                if (sourceNodeId === containerId) return;
                if (nodeContainsId(sourceLoc.node, containerId)) {
                    ElMessage.warning("不能将容器拖放到自身或子容器中");
                    return;
                }

                sourceLoc.parentList.splice(sourceLoc.index, 1);
                if (!Array.isArray(containerLoc.node.children)) {
                    containerLoc.node.children = [];
                }
                containerLoc.node.children.push(sourceLoc.node);
            };

            const moveNodeToCanvasEnd = (sourceNodeId) => {
                const form = activeForm.value;
                if (!form || !sourceNodeId) return;
                const sourceLoc = findNodeLocation(form, sourceNodeId);
                if (!sourceLoc) return;
                const node = sourceLoc.node;
                sourceLoc.parentList.splice(sourceLoc.index, 1);
                form.nodes.push(node);
            };

            const onNodeDrop = (targetNodeId) => {
                if (!activeForm.value) return;
                if (dragState.mode === "palette" && dragState.paletteComponent) {
                    addNodeToForm(dragState.paletteComponent, "", targetNodeId);
                    clearDragState();
                    return;
                }
                if (dragState.mode === "move" && dragState.sourceNodeId) {
                    moveNodeBeforeTarget(dragState.sourceNodeId, targetNodeId);
                    clearDragState();
                }
            };

            const onContainerDrop = (containerId) => {
                if (!activeForm.value) return;
                if (dragState.mode === "palette" && dragState.paletteComponent) {
                    addNodeToForm(dragState.paletteComponent, containerId);
                    clearDragState();
                    return;
                }
                if (dragState.mode === "move" && dragState.sourceNodeId) {
                    moveNodeIntoContainer(dragState.sourceNodeId, containerId);
                    clearDragState();
                }
            };

            const onCanvasDrop = () => {
                if (!activeForm.value) return;
                if (dragState.mode === "palette" && dragState.paletteComponent) {
                    addNodeToForm(dragState.paletteComponent);
                    clearDragState();
                    return;
                }
                if (dragState.mode === "move" && dragState.sourceNodeId) {
                    moveNodeToCanvasEnd(dragState.sourceNodeId);
                    clearDragState();
                }
            };

            const onCanvasDragOver = (event) => {
                if (!isDraggingActive.value) return;
                const target = event?.target;
                if (target?.closest && !target.closest(".fd-container")) {
                    dragState.overContainerId = "";
                }
            };

            const moveNode = (nodeId, delta) => {
                const form = activeForm.value;
                if (!form) return;
                const location = findNodeLocation(form, nodeId);
                if (!location) return;
                const targetIndex = location.index + delta;
                if (targetIndex < 0 || targetIndex >= location.parentList.length) return;
                const list = location.parentList;
                const current = list[location.index];
                list[location.index] = list[targetIndex];
                list[targetIndex] = current;
            };

            const cloneNodeWithNewIds = (rawNode) => {
                const cloned = deepClone(rawNode);
                const renew = (node) => {
                    node.id = nextId("node");
                    if (Array.isArray(node.options)) {
                        node.options = node.options.map((opt) => ({
                            id: nextId("option"),
                            label: opt?.label ?? "",
                            value: opt?.value ?? "",
                        }));
                    }
                    if (node.component === "container") {
                        node.layout_mode = "grid";
                        delete node.flex_direction;
                        delete node.justify_content;
                        delete node.align_items;
                        delete node.flex_wrap;
                        if (Array.isArray(node.children)) {
                            node.children = node.children.map((child) => renew(child));
                        } else {
                            node.children = [];
                        }
                    }
                    return node;
                };
                return renew(cloned);
            };

            const copyNode = (nodeId) => {
                const form = activeForm.value;
                if (!form) return;
                const location = findNodeLocation(form, nodeId);
                if (!location) return;
                const copied = cloneNodeWithNewIds(location.node);
                location.parentList.splice(location.index + 1, 0, copied);
                selectedNodeId.value = copied.id;
            };

            const removeNode = (nodeId) => {
                const form = activeForm.value;
                if (!form) return;
                const location = findNodeLocation(form, nodeId);
                if (!location) return;
                location.parentList.splice(location.index, 1);
                if (selectedNodeId.value === nodeId) {
                    selectedNodeId.value = "";
                }
            };

            const addOption = (node) => {
                if (!node) return;
                if (!Array.isArray(node.options)) {
                    node.options = [];
                }
                node.options.push(createOption());
            };

            const removeOption = (node, index) => {
                if (!node || !Array.isArray(node.options)) return;
                node.options.splice(index, 1);
            };

            const moveOption = (node, index, delta) => {
                if (!node || !Array.isArray(node.options)) return;
                const target = index + delta;
                if (target < 0 || target >= node.options.length) return;
                const list = node.options;
                const current = list[index];
                list[index] = list[target];
                list[target] = current;
            };

            const toInlineStyle = (styleObject = {}) =>
                Object.entries(styleObject)
                    .filter(([, value]) => value !== undefined && value !== null && value !== "")
                    .map(([key, value]) => `${key}:${value}`)
                    .join(";");

            const containerStyle = (node) => {
                if (!node || node.component !== "container") return "";
                const base = {
                    padding: `${Math.max(0, Number(node.padding || 0))}px`,
                    gap: `${Math.max(0, Number(node.gap || 0))}px`,
                    display: "grid",
                };
                const columns = Math.max(1, Number(node.grid_columns || 1));
                base["grid-template-columns"] = `repeat(${columns}, minmax(0, 1fr))`;
                const merged = toInlineStyle(base);
                if (node.css_text) return `${merged};${node.css_text}`;
                return merged;
            };

            const showPlaceholder = (node) => {
                if (!node || node.component === "container") return false;
                if (DISPLAY_COMPONENTS.has(node.component)) return false;
                return !["switch", "checkbox", "radio", "file", "signature"].includes(node.component);
            };

            const showDefaultField = (node) => {
                if (!node || node.component === "container") return false;
                if (DISPLAY_COMPONENTS.has(node.component)) return false;
                if (node?.default_source_ui?.mode !== "fixed") return false;
                return !["switch", "file", "checkbox", "signature"].includes(node.component);
            };

            const isTextComponent = (node) => !!node && TEXT_COMPONENTS.has(node.component);
            const isStructureDisplayComponent = (node) => !!node && STRUCTURE_DISPLAY_COMPONENTS.has(node.component);
            const hasSourceAwareDisplayContent = (node) => !!node && SOURCE_AWARE_DISPLAY_COMPONENTS.has(node.component);
            const isVariableComponent = (node) => !!node && VARIABLE_COMPONENTS.has(node.component);
            const resolveVariablePreviewText = (node) => {
                if (!node || !VARIABLE_COMPONENTS.has(node.component)) return "";
                const variableMeta = VARIABLE_META_MAP[node.component] || { key: "" };
                const variableKey = String(node.variable_key || variableMeta.key || "").trim();
                const value = resolveVariableValueByKey(variableKey);
                return value === undefined || value === null || value === "" ? "-" : String(value);
            };

            const validateNodes = (nodes, formName, existedKeys) => {
                for (const node of nodes || []) {
                    if (!node || typeof node !== "object") continue;

                    if (node.component === "container") {
                        const containerLabel = String(node.label || "").trim();
                        if (!containerLabel) {
                            ElMessage.error(`Form [${formName}] has a container with empty label`);
                            return false;
                        }
                        if (!validateNodes(node.children || [], formName, existedKeys)) {
                            return false;
                        }
                        continue;
                    }

                    if (DISPLAY_COMPONENTS.has(node.component)) {
                        continue;
                    }

                    const key = String(node.key || "").trim();
                    const label = String(node.label || "").trim();
                    if (!key || !label) {
                        ElMessage.error(`Form [${formName}] has incomplete field config`);
                        return false;
                    }
                    if (existedKeys.has(key)) {
                        ElMessage.error(`Form [${formName}] has duplicate field key: ${key}`);
                        return false;
                    }
                    existedKeys.add(key);

                    if (["select", "radio", "checkbox"].includes(node.component)) {
                        const requiresManualOptions = usesManualOptions(node);
                        if (requiresManualOptions && (!Array.isArray(node.options) || !node.options.length)) {
                            ElMessage.error(`Form [${formName}] field [${label}] requires at least one option`);
                            return false;
                        }
                        if (requiresManualOptions) {
                            for (const option of node.options) {
                                const optionLabel = String(option?.label ?? "").trim();
                                const optionValue = option?.value;
                                if (!optionLabel || optionValue === "" || optionValue === null || optionValue === undefined) {
                                    ElMessage.error(`Form [${formName}] field [${label}] has empty option`);
                                    return false;
                                }
                            }
                        }
                    }

                    if (node.component === "number") {
                        if (node.min !== undefined && node.max !== undefined && Number(node.min) > Number(node.max)) {
                            ElMessage.error(`Form [${formName}] field [${label}] has min greater than max`);
                            return false;
                        }
                    }
                }
                return true;
            };

            const validateBeforeSave = () => {
                if (!forms.length) {
                    ElMessage.error("请至少创建一张表单");
                    return false;
                }

                const formCodeSet = new Set();
                for (const form of forms) {
                    const code = String(form.code || "").trim();
                    const name = String(form.name || "").trim();
                    if (!code || !name) {
                        ElMessage.error("表单编码和表单名称不能为空");
                        return false;
                    }
                    if (formCodeSet.has(code)) {
                        ElMessage.error(`表单编码重复: ${code}`);
                        return false;
                    }
                    formCodeSet.add(code);

                    const existedKeys = new Set();
                    if (!validateNodes(form.nodes || [], name, existedKeys)) {
                        return false;
                    }
                }
                return true;
            };

            const buildPayloadNode = (node, index = 0) => {
                const payload = {
                    component: node.component,
                    label: String(node.label || "").trim(),
                    order: index,
                };
                if (node.css_text) payload.css_text = node.css_text;
                if (node.js_text) payload.js_text = node.js_text;

                if (node.component === "container") {
                    payload.layout_mode = "grid";
                    payload.grid_columns = Math.max(1, Number(node.grid_columns || 1));
                    payload.gap = Math.max(0, Number(node.gap || 0));
                    payload.padding = Math.max(0, Number(node.padding || 0));
                    payload.children = (node.children || []).map((child, childIndex) => buildPayloadNode(child, childIndex));
                    return payload;
                }

                if (TEXT_COMPONENTS.has(node.component)) {
                    if (node?.default_source_ui?.mode === "fixed") {
                        payload.content = String(node.content || node.label || "").trim();
                    }
                    Object.assign(payload, buildDefaultSourcePayload(node));
                    payload.text_align = String(node.text_align || "left");
                    payload.text_v_align = String(node.text_v_align || "top");
                    payload.text_min_height = Math.max(0, Number(node.text_min_height || 0));
                    return payload;
                }

                if (STRUCTURE_DISPLAY_COMPONENTS.has(node.component)) {
                    if (node.component === "divider") {
                        const lineThicknessRaw = Number(node.line_thickness);
                        const lineMarginRaw = Number(node.line_margin);
                        payload.line_style = String(node.line_style || "solid");
                        payload.line_color = String(node.line_color || "#d7deea");
                        payload.line_thickness = Number.isFinite(lineThicknessRaw) ? Math.max(1, lineThicknessRaw) : 1;
                        payload.line_margin = Number.isFinite(lineMarginRaw) ? Math.max(0, lineMarginRaw) : 12;
                        return payload;
                    }
                    if (node.component === "spacer") {
                        const heightRaw = Number(node.height);
                        payload.height = Number.isFinite(heightRaw) ? Math.max(0, heightRaw) : 24;
                        return payload;
                    }
                    if (node.component === "section_header") {
                        if (node?.default_source_ui?.mode === "fixed") {
                            payload.content = String(node.content || node.label || "").trim();
                        }
                        payload.sub_content = String(node.sub_content || "").trim();
                        Object.assign(payload, buildDefaultSourcePayload(node));
                        return payload;
                    }
                    if (node.component === "card_block") {
                        const paddingRaw = Number(node.card_padding);
                        const radiusRaw = Number(node.card_radius);
                        payload.title = String(node.title || node.label || "信息卡片").trim();
                        if (node?.default_source_ui?.mode === "fixed") {
                            payload.content = String(node.content || "").trim();
                        }
                        payload.card_padding = Number.isFinite(paddingRaw) ? Math.max(0, paddingRaw) : 12;
                        payload.card_radius = Number.isFinite(radiusRaw) ? Math.max(0, radiusRaw) : 10;
                        payload.card_shadow = !!node.card_shadow;
                        Object.assign(payload, buildDefaultSourcePayload(node));
                        return payload;
                    }
                }

                if (VARIABLE_COMPONENTS.has(node.component)) {
                    const variableMeta = VARIABLE_META_MAP[node.component] || { key: "" };
                    payload.variable_key = String(node.variable_key || variableMeta.key || "").trim();
                    payload.variable_label = String(node.variable_label || node.label || "").trim();
                    return payload;
                }

                payload.key = String(node.key || "").trim();
                payload.disabled = !!node.disabled;
                payload.required = !!node.required;

                if (node.placeholder) payload.placeholder = node.placeholder;
                if (node?.default_source_ui?.mode === "fixed" && node.default !== "" && node.default !== null && node.default !== undefined) {
                    payload.default = node.default;
                }
                Object.assign(payload, buildDefaultSourcePayload(node));

                Object.assign(payload, buildContextBindingPayload(node));

                if (node.component === "textarea" && node.rows) {
                    payload.rows = node.rows;
                }
                if (node.component === "number") {
                    if (node.min !== undefined && node.min !== null && node.min !== "") payload.min = Number(node.min);
                    if (node.max !== undefined && node.max !== null && node.max !== "") payload.max = Number(node.max);
                    if (node.step !== undefined && node.step !== null && node.step !== "") payload.step = Number(node.step);
                }
                if (node.component === "file") {
                    if (node.accept) payload.accept = node.accept;
                    if (node.multiple) payload.multiple = true;
                }
                if (["select", "radio", "checkbox"].includes(node.component)) {
                    if (usesManualOptions(node)) {
                        payload.options = (node.options || []).map((option) => ({
                            label: String(option.label || "").trim(),
                            value: option.value,
                        }));
                    }
                    Object.assign(payload, buildOptionsSourcePayload(node));
                }
                return payload;
            };

            const buildPayloadForms = () =>
                forms.map((form, index) => ({
                    code: String(form.code || "").trim(),
                    name: String(form.name || "").trim(),
                    group_name: String(form.group_name || "").trim(),
                    description: String(form.description || "").trim(),
                    order: index,
                    fields: (form.nodes || []).map((node, nodeIndex) => buildPayloadNode(node, nodeIndex)),
                }));

            const buildJsonPayload = () => ({
                forms: buildPayloadForms(),
            });

            const buildPreviewFormData = (nodes) => {
                const data = {};
                const travel = (list) => {
                    for (const node of list || []) {
                        if (!node || typeof node !== "object") continue;
                        if (node.component === "container") {
                            travel(node.children || []);
                            continue;
                        }
                        if (DISPLAY_COMPONENTS.has(node.component)) {
                            continue;
                        }
                        if (!node.key) continue;
                        if (node.default !== undefined && node.default !== null && node.default !== "") {
                            data[node.key] = Array.isArray(node.default) ? [...node.default] : node.default;
                            continue;
                        }
                        if (node.component === "switch") {
                            data[node.key] = false;
                        } else if (node.component === "checkbox") {
                            data[node.key] = [];
                        } else if (node.component === "file" && node.multiple) {
                            data[node.key] = [];
                        } else {
                            data[node.key] = "";
                        }
                    }
                };
                travel(nodes || []);
                return data;
            };

            const buildPreviewRules = (nodes) => {
                const rules = {};
                const travel = (list) => {
                    for (const node of list || []) {
                        if (!node || typeof node !== "object") continue;
                        if (node.component === "container") {
                            travel(node.children || []);
                            continue;
                        }
                        if (DISPLAY_COMPONENTS.has(node.component)) {
                            continue;
                        }
                        const key = String(node.key || "").trim();
                        if (!key || !node.required) continue;
                        const message = `${node.label || key} 为必填项`;
                        if (node.component === "checkbox") {
                            rules[key] = [{ required: true, type: "array", min: 1, message, trigger: "change" }];
                        } else {
                            rules[key] = [{ required: true, message, trigger: "change" }];
                        }
                    }
                };
                travel(nodes || []);
                return rules;
            };

            const runFieldScript = (field, value, formData) => {
                const script = String(field?.js_text || "").trim();
                if (!script) return;
                try {
                    const helpers = {
                        setValue: (key, val) => {
                            formData[key] = val;
                        },
                        getValue: (key) => formData[key],
                        message: (msg, type = "info") => {
                            ElMessage({
                                message: String(msg || ""),
                                type,
                            });
                        },
                    };
                    const fn = new Function("value", "formData", "field", "helpers", script);
                    const result = fn(value, formData, field, helpers);
                    if (result !== undefined && field?.key) {
                        formData[field.key] = result;
                    }
                } catch (err) {
                    console.error(err);
                    ElMessage.error(`${field?.label || field?.key || "字段"} 脚本执行失败`);
                }
            };

            const buildRuntimePreviewSchema = (nodes) => ({
                fields: (nodes || []).map((node, index) => buildPayloadNode(node, index)),
            });

            const extractPreviewNodesFromSchema = (schema) => {
                if (Array.isArray(schema)) return schema;
                if (Array.isArray(schema?.fields)) return schema.fields;
                if (Array.isArray(schema?.form?.fields)) return schema.form.fields;
                if (Array.isArray(schema?.schema?.fields)) return schema.schema.fields;
                return [];
            };

            const ensurePreviewNodeIds = (nodes) => {
                let counter = 0;
                const walk = (list, prefix = "preview") => {
                    (list || []).forEach((node) => {
                        if (!node || typeof node !== "object") return;
                        if (!node.id) {
                            node.id = `${prefix}_${counter += 1}`;
                        }
                        if (node.component === "container" && Array.isArray(node.children)) {
                            walk(node.children, node.id);
                        }
                    });
                };
                walk(nodes);
                return nodes;
            };

            const parsePreviewContext = () => {
                const raw = String(previewDialog.contextText || "").trim();
                if (!raw) return {};
                try {
                    const parsed = JSON.parse(raw);
                    return parsed && typeof parsed === "object" ? parsed : {};
                } catch (err) {
                    console.error(err);
                    ElMessage.error("预览上下文 JSON 解析失败");
                    return null;
                }
            };

            const resolveRuntimePreview = async (nodes, contextOverride) => {
                const context = contextOverride !== undefined ? contextOverride : parsePreviewContext();
                if (context === null) {
                    throw new Error("preview_context_invalid");
                }
                const payload = {
                    form_schema: buildRuntimePreviewSchema(nodes),
                    context,
                    node_code: String(activeForm.value?.code || ""),
                    runtime_env: {
                        preview: true,
                    },
                };
                const res = await request.post("/flow_engine/form_runtime_preview_resolve", payload);
                const data = res?.data ?? res ?? {};
                const resolvedSchema = data.resolved_form_schema || {};
                const resolvedFormData = data.resolved_form_data || {};
                const resolvedNodes = extractPreviewNodesFromSchema(resolvedSchema);
                return {
                    resolvedNodes,
                    resolvedFormData,
                };
            };

            const applyPreviewState = (nodes, formData) => {
                previewDialog.nodes = nodes;
                previewDialog.formData = formData;
                previewDialog.rules = buildPreviewRules(nodes);
                previewDialog.submittedJson = "";
            };

            const loadFormLibrary = async () => {
                const res = await request.get("/flow_engine/form_global_detail");
                const rawForms = Array.isArray(res?.forms) ? res.forms : [];
                setFormsFromRaw(rawForms, 0);
                if (selectedFormCodeFromQuery) {
                    const idx = forms.findIndex((item) => String(item.code || "").trim() === selectedFormCodeFromQuery);
                    if (idx >= 0) {
                        setActiveForm(idx);
                    }
                }
            };

            const saveFormLibrary = async () => {
                if (pageData.saving) return;
                if (!validateBeforeSave()) return;
                pageData.saving = true;
                try {
                    const payloadForms = buildPayloadForms();
                    const res = await request.post("/flow_engine/form_global_save", {
                        forms: payloadForms,
                    });

                    const savedForms = Array.isArray(res?.forms) ? res.forms : payloadForms;
                    const safeIndex = selectedFormIndex.value;
                    setFormsFromRaw(savedForms, safeIndex >= 0 ? safeIndex : 0);
                    clearDraft();
                    pushHistorySnapshot();

                    ElMessage.success("表单库保存成功");
                } finally {
                    pageData.saving = false;
                }
            };

            const openPreviewDialog = async () => {
                if (!activeForm.value) return;
                let sourceNodes = [];
                try {
                    sourceNodes = deepClone(activeForm.value.nodes || []);
                } catch {
                    sourceNodes = Array.isArray(activeForm.value.nodes) ? [...activeForm.value.nodes] : [];
                }
                if (!sourceNodes.length && Array.isArray(activeForm.value.nodes) && activeForm.value.nodes.length) {
                    sourceNodes = activeForm.value.nodes;
                }
                previewDialog.sourceNodes = sourceNodes;
                if (!String(previewDialog.contextText || "").trim()) {
                    previewDialog.contextText = "{}";
                }
                try {
                    const { resolvedNodes, resolvedFormData } = await resolveRuntimePreview(sourceNodes);
                    if (Array.isArray(resolvedNodes) && resolvedNodes.length) {
                        const nodes = ensurePreviewNodeIds(resolvedNodes);
                        const data = (resolvedFormData && typeof resolvedFormData === "object")
                            ? resolvedFormData
                            : buildPreviewFormData(nodes);
                        applyPreviewState(nodes, data);
                        previewDialog.visible = true;
                        return;
                    }
                } catch (err) {
                    console.error(err);
                }
                applyPreviewState(sourceNodes, buildPreviewFormData(sourceNodes));
                previewDialog.visible = true;
            };

            const submitPreviewForm = async () => {
                if (!previewFormRef.value) return;
                try {
                    await previewFormRef.value.validate();
                    previewDialog.submittedJson = JSON.stringify(previewDialog.formData, null, 2);
                    ElMessage.success("预览提交成功");
                } catch {
                    ElMessage.warning("请先填写必填字段");
                }
            };

            const resetPreviewForm = async () => {
                const sourceNodes = Array.isArray(previewDialog.sourceNodes) && previewDialog.sourceNodes.length
                    ? previewDialog.sourceNodes
                    : (Array.isArray(activeForm.value?.nodes) ? activeForm.value.nodes : []);
                try {
                    const { resolvedNodes, resolvedFormData } = await resolveRuntimePreview(sourceNodes);
                    if (Array.isArray(resolvedNodes) && resolvedNodes.length) {
                        const nodes = ensurePreviewNodeIds(resolvedNodes);
                        const data = (resolvedFormData && typeof resolvedFormData === "object")
                            ? resolvedFormData
                            : buildPreviewFormData(nodes);
                        applyPreviewState(nodes, data);
                    } else {
                        applyPreviewState(sourceNodes, buildPreviewFormData(sourceNodes));
                    }
                } catch (err) {
                    console.error(err);
                    applyPreviewState(sourceNodes, buildPreviewFormData(sourceNodes));
                }
                if (previewFormRef.value?.clearValidate) {
                    previewFormRef.value.clearValidate();
                }
            };

            const applyPreviewContext = async () => {
                const sourceNodes = Array.isArray(previewDialog.sourceNodes) && previewDialog.sourceNodes.length
                    ? previewDialog.sourceNodes
                    : (Array.isArray(activeForm.value?.nodes) ? activeForm.value.nodes : []);
                try {
                    const { resolvedNodes, resolvedFormData } = await resolveRuntimePreview(sourceNodes);
                    if (Array.isArray(resolvedNodes) && resolvedNodes.length) {
                        const nodes = ensurePreviewNodeIds(resolvedNodes);
                        const data = (resolvedFormData && typeof resolvedFormData === "object")
                            ? resolvedFormData
                            : buildPreviewFormData(nodes);
                        applyPreviewState(nodes, data);
                    } else {
                        applyPreviewState(sourceNodes, buildPreviewFormData(sourceNodes));
                    }
                } catch (err) {
                    if (err?.message !== "preview_context_invalid") {
                        console.error(err);
                    }
                }
                if (previewFormRef.value?.clearValidate) {
                    previewFormRef.value.clearValidate();
                }
            };

            const onPreviewFileChange = ({ field, files }) => {
                if (!field?.key) return;
                const values = (files || []).map((file) => file.name);
                const value = field.multiple ? values : (values[0] || "");
                previewDialog.formData[field.key] = value;
                runFieldScript(field, value, previewDialog.formData);
            };

            const copyJsonText = async (text) => {
                const content = String(text || "");
                if (!content) return;
                try {
                    if (navigator?.clipboard?.writeText) {
                        await navigator.clipboard.writeText(content);
                    } else {
                        const input = document.createElement("textarea");
                        input.value = content;
                        document.body.appendChild(input);
                        input.select();
                        document.execCommand("copy");
                        document.body.removeChild(input);
                    }
                    ElMessage.success("数据已复制到剪贴板");
                } catch (err) {
                    console.error(err);
                    ElMessage.error("复制失败，请手动复制");
                }
            };

            const openJsonDialog = () => {
                jsonDialog.content = JSON.stringify(buildJsonPayload(), null, 2);
                jsonDialog.visible = true;
            };

            const copyJsonPayload = () => {
                copyJsonText(JSON.stringify(buildJsonPayload(), null, 2));
            };

            const downloadJsonFile = () => {
                const content = JSON.stringify(buildJsonPayload(), null, 2);
                const blob = new Blob([content], {
                    type: "application/json;charset=utf-8",
                });
                const anchor = document.createElement("a");
                const stamp = new Date().toISOString().replace(/[:.]/g, "-");
                anchor.href = URL.createObjectURL(blob);
                anchor.download = `flow-form-${flowId || "draft"}-${stamp}.json`;
                document.body.appendChild(anchor);
                anchor.click();
                document.body.removeChild(anchor);
                URL.revokeObjectURL(anchor.href);
            };

            const importJsonFile = async () => {
                const input = document.createElement("input");
                input.type = "file";
                input.accept = ".json,application/json";
                input.onchange = async (event) => {
                    const file = event?.target?.files?.[0];
                    if (!file) return;
                    try {
                        const text = await file.text();
                        jsonDialog.content = text;
                        applyJsonContent();
                    } catch (err) {
                        console.error(err);
                        ElMessage.error("读取数据文件失败");
                    }
                };
                input.click();
            };

            const applyJsonContent = () => {
                let parsed;
                try {
                    parsed = JSON.parse(jsonDialog.content || "{}");
                } catch {
                    ElMessage.error("数据格式不正确");
                    return;
                }

                const rawForms = Array.isArray(parsed)
                    ? parsed
                    : Array.isArray(parsed?.forms)
                        ? parsed.forms
                        : [];

                setFormsFromRaw(rawForms, 0);
                pushHistorySnapshot();
                saveDraftToLocal();

                jsonDialog.visible = false;
                ElMessage.success("数据已应用到当前页面");
            };

            const restoreLocalDraft = async () => {
                let draft = null;
                try {
                    draft = JSON.parse(localStorage.getItem(getDraftStorageKey()) || "null");
                } catch {
                    draft = null;
                }
                const rawForms = Array.isArray(draft?.payload?.forms) ? draft.payload.forms : [];
                if (!rawForms.length) return;
                if (JSON.stringify(rawForms) === JSON.stringify(buildPayloadForms())) return;
                if (ElMessageBox?.confirm) {
                    try {
                        await ElMessageBox.confirm(
                            "检测到本地草稿，是否恢复到编辑器？",
                            "恢复草稿",
                            {
                                type: "warning",
                                confirmButtonText: "恢复",
                                cancelButtonText: "忽略",
                            },
                        );
                    } catch {
                        return;
                    }
                }
                setFormsFromRaw(rawForms, selectedFormIndex.value >= 0 ? selectedFormIndex.value : 0);
                pushHistorySnapshot();
                ElMessage.success("本地草稿已恢复");
            };

            const clearActiveForm = async () => {
                const form = activeForm.value;
                if (!form) return;
                if (!form.nodes.length) {
                    ElMessage.info("当前表单已经是空表单");
                    return;
                }

                const doClear = () => {
                    form.nodes.splice(0, form.nodes.length);
                    selectedNodeId.value = "";
                    ElMessage.success("当前表单已清空");
                };

                if (ElMessageBox?.confirm) {
                    try {
                        await ElMessageBox.confirm("确定要清空当前表单的所有组件吗？", "确认", {
                            type: "warning",
                            confirmButtonText: "确定",
                            cancelButtonText: "取消",
                        });
                        doClear();
                    } catch {
                        return;
                    }
                    return;
                }
                doClear();
            };

            const goBack = () => {
                window.location.href = previousUrl || "/admin/flow_engine/form/list/";
            };

            const consumeCreateQuery = () => {
                if (!shouldCreateFormFromQuery) return;
                const nextParams = new URLSearchParams(window.location.search || "");
                nextParams.delete("new_form");
                nextParams.delete("group_name");
                const nextQuery = nextParams.toString();
                const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}`;
                window.history.replaceState({}, "", nextUrl);
            };

            const gotoFlowDesigner = () => {
                if (!flowId) {
                    window.location.href = "/admin/flow_engine/definition/list/";
                    return;
                }
                window.location.href = `/admin/flow_engine/definition/${flowId}/change/`;
            };

            watch(
                forms,
                () => {
                    scheduleAutoCapture();
                },
                { deep: true },
            );

            watch(
                () => paletteState.tab,
                (value) => {
                    if (!paletteTabSet.has(value)) {
                        paletteState.tab = "all";
                    }
                },
            );

            watch([selectedFormIndex, selectedNodeId, activeRightTab], () => {
                scheduleAutoCapture();
            });

            onMounted(async () => {
                await fetchFieldDataSourceMetadata();
                paletteState.tab = "all";
                paletteState.keyword = "";
                try {
                    await loadFormLibrary();
                    if (shouldCreateFormFromQuery) {
                        addForm();
                        consumeCreateQuery();
                    }
                    pushHistorySnapshot();
                    pageData.pageLoading = false;
                    if (!shouldCreateFormFromQuery) {
                        await restoreLocalDraft();
                    }
                } finally {
                    pageData.pageLoading = false;
                }
                window.addEventListener("dragend", clearDragState);
            });

            onBeforeUnmount(() => {
                window.removeEventListener("dragend", clearDragState);
                if (historyCaptureTimer) clearTimeout(historyCaptureTimer);
                if (draftSaveTimer) clearTimeout(draftSaveTimer);
            });

            return {
                pageData,
                previewDialog,
                previewFormRef,
                previewNodes,
                previewHasNodes,
                jsonDialog,
                componentGroups,
                paletteState,
                filteredComponentGroups,
                forms,
                selectedFormIndex,
                selectedFormIndexValue,
                selectedNodeId,
                selectedNode,
                activeForm,
                activeFormNodeCount,
                activeRightTab,
                canUndo,
                canRedo,
                goBack,
                gotoFlowDesigner,
                undo,
                redo,
                onSelectFormByValue,
                addForm,
                removeForm,
                componentLabel,
                onPaletteDragStart,
                onNodeDragStart,
                onNodeDrop,
                onCanvasDrop,
                onCanvasDragOver,
                onContainerDrop,
                onContainerDragOver,
                onContainerDragLeave,
                isContainerDropActive,
                onNodeDragEnter,
                isNodeDropTarget,
                addComponentByClick,
                selectNode,
                moveNode,
                copyNode,
                removeNode,
                addOption,
                moveOption,
                removeOption,
                fieldDataSourceMetadata,
                getDefaultFieldDataSources,
                getOptionsFieldDataSources,
                hasCompatibleFieldDataSources,
                getCurrentFieldDataSourceOptions,
                getCurrentFieldDataSourcePagedOptions,
                getFieldDataSourceKeyLabel,
                getSourceParamsSchema,
                fieldDataSourcePicker,
                onFieldDataSourceChange,
                openFieldDataSourcePicker,
                closeFieldDataSourcePicker,
                chooseFieldDataSource,
                applyFieldDataSourceSelection,
                clearFieldDataSourceSelection,
                clearFieldDataSource,
                onFieldDataSourcePickerKeywordChange,
                buildFieldDataSourcePlaceholder,
                usesManualOptions,
                containerStyle,
                showPlaceholder,
                showDefaultField,
                isTextComponent,
                isStructureDisplayComponent,
                hasSourceAwareDisplayContent,
                isVariableComponent,
                resolveVariablePreviewText,
                saveFormLibrary,
                openPreviewDialog,
                submitPreviewForm,
                resetPreviewForm,
                applyPreviewContext,
                onPreviewFileChange,
                runFieldScript,
                openJsonDialog,
                applyJsonContent,
                copyJsonPayload,
                copyJsonText,
                downloadJsonFile,
                importJsonFile,
                clearActiveForm,
            };
        },
    });
}
