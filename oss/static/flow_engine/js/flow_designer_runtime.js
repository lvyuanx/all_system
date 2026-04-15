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
} from "./field_source_designer.js";
import {
    APPROVAL_MODE_OPTIONS,
    buildFieldDataSourcePlaceholder,
    FORM_REF_CODE_KEY,
    FORM_REF_NAME_KEY,
    NODE_TYPE_OPTIONS,
    RULE_TYPE_OPTIONS,
} from "./flow_designer_constants.js";

export function mountFlowDesigner(options = {}) {
    const { reactive, ref, computed, onMounted, onBeforeUnmount, inject, nextTick } = Vue;
    const previousUrl = options.previousUrl || "";
    const initialFlowId = options.flowId || "";
    const initialFieldDataSourceMetadata = options.fieldDataSourceMetadata || [];

    window.createApp({
        setup() {
            const fieldDataSourceMetadata = normalizeFieldDataSourceMetadata(
                initialFieldDataSourceMetadata
            );
            const ElMessage = inject("ElMessage");
            const goBack = () => {
                window.location.href = previousUrl;
            };

            const flowId = ref(String(initialFlowId || ""));
            const pageData = reactive({
                pageLoading: true,
                saving: false,
                publishing: false,
            });
            const flowFormRef = ref(null);
            const canvasWrapRef = ref(null);
            const canvasBoardRef = ref(null);
            const importFileRef = ref(null);

            const importDialog = reactive({
                visible: false,
                overwrite: false,
                text: "",
            });

            const flowForm = reactive({
                code: "",
                name: "",
                description: "",
                is_active: true,
            });

            const flowRules = reactive({
                code: [{ required: true, message: "请输入流程编码", trigger: "blur" }],
                name: [{ required: true, message: "请输入流程名称", trigger: "blur" }],
            });

            const nodes = reactive([]);
            const transitions = reactive([]);

            const selectedNodeIndex = ref(-1);
            const selectedEdgeIndex = ref(-1);
            const hoveredEdgeIndex = ref(-1);

            const connectMode = ref(false);
            const connectState = reactive({
                fromIndex: -1,
                mouseX: 0,
                mouseY: 0,
            });
            const dragState = reactive({
                active: false,
                nodeIndex: -1,
                offsetX: 0,
                offsetY: 0,
            });

            const nodeRefMap = new WeakMap();

            const nodeTypeOptions = NODE_TYPE_OPTIONS;
            const approvalModeOptions = APPROVAL_MODE_OPTIONS;
            const ruleTypeOptions = RULE_TYPE_OPTIONS;

            const permPackOptions = ref([]);
            const userOptions = ref([]);
            const userLoading = ref(false);
            const formLibrary = reactive([]);
            const globalFormLibrary = reactive([]);
            const formLibraryOptions = computed(() =>
                (globalFormLibrary.length ? globalFormLibrary : formLibrary).map((item) => ({
                    code: item.code,
                    name: `${item.name || item.code}${item.code ? ` (${item.code})` : ""}`,
                }))
            );

            const NODE_WIDTH = 220;
            const NODE_HEIGHT = 100;
            let formFieldSeed = 1;

            const nodeDialog = reactive({
                visible: false,
                editIndex: -1,
                dragIndex: -1,
                form: {
                    code: "",
                    name: "",
                    node_type: "task",
                    approval_mode: "any",
                    is_auto: false,
                    order: 0,
                    x: 120,
                    y: 120,
                    form_schema_text: "",
                    form_schema: null,
                    form_ref_code: "",
                    form_fields: [],
                    legacy_form_schema: null,
                    groups: [],
                },
            });

            const currentNodeFormRefName = computed(() => {
                const refCode = nodeDialog.form?.form_ref_code || "";
                if (!refCode) return "";
                const source = globalFormLibrary.length ? globalFormLibrary : formLibrary;
                const matched = source.find((item) => item.code === refCode);
                return matched?.name || "";
            });

            const selectedNode = computed(() => {
                if (selectedNodeIndex.value < 0) return null;
                return nodes[selectedNodeIndex.value];
            });

            const selectedEdge = computed(() => {
                if (selectedEdgeIndex.value < 0) return null;
                return transitions[selectedEdgeIndex.value];
            });

            const setNodeRef = (node, el) => {
                if (!node || typeof node !== "object") return;
                if (el) {
                    nodeRefMap.set(node, el);
                }
            };

            const nodeTypeLabel = (value) => {
                const item = nodeTypeOptions.find((it) => it.value === value);
                return item ? item.label : value;
            };

            const formatUserLabel = (u) => {
                const name = u.full_name || "";
                const phone = u.phone ? `(${u.phone})` : "";
                return `${name}${phone}`;
            };

            const searchUsers = async (keyword) => {
                userLoading.value = true;
                try {
                    userOptions.value = await request.get("/flow_engine/user_list", { keyword });
                } finally {
                    userLoading.value = false;
                }
            };

            const loadOptions = async () => {
                permPackOptions.value = await request.get("/flow_engine/perm_pack_list");
                await searchUsers("");
            };

            const deepClone = (obj) => JSON.parse(JSON.stringify(obj));

            const stripUi = (schema) => {
                if (!schema || typeof schema !== "object") return null;
                const cloned = deepClone(schema);
                delete cloned.__ui;
                delete cloned.__form_library;
                return Object.keys(cloned).length ? cloned : null;
            };

            const normalizeLibraryFields = (fields) => {
                const raw = Array.isArray(fields) ? fields : [];
                return raw
                    .map((field, index) => {
                        const key = (field?.key || field?.name || field?.prop || "").toString().trim();
                        const label = (field?.label || field?.title || field?.name || "").toString().trim();
                        if (!key || !label) return null;
                        const component = (field?.component || field?.widget || field?.type || "input").toString();
                        const payload = {
                            key,
                            label,
                            component,
                            required: !!field?.required,
                            order: Number.isFinite(Number(field?.order)) ? Number(field.order) : index,
                        };
                        if (field?.placeholder) payload.placeholder = field.placeholder;
                        if ((field?.default_source_ui?.mode || "fixed") === "fixed" && Object.prototype.hasOwnProperty.call(field || {}, "default")) {
                            payload.default = field.default;
                        }
                        if (
                            (field?.default_source_ui?.mode || "fixed") === "fixed"
                            && Object.prototype.hasOwnProperty.call(field || {}, "default_value")
                            && !Object.prototype.hasOwnProperty.call(payload, "default")
                        ) {
                            payload.default = field.default_value;
                        }
                        if (field?.default_config && typeof field.default_config === "object") {
                            payload.default_config = deepClone(field.default_config);
                        }
                        if (field?.default_source_config && typeof field.default_source_config === "object") {
                            payload.default_source_config = deepClone(field.default_source_config);
                        }
                        if (field?.context_binding && typeof field.context_binding === "object") {
                            payload.context_binding = deepClone(field.context_binding);
                        }
                        if (field?.options_config && typeof field.options_config === "object") {
                            payload.options_config = deepClone(field.options_config);
                        }
                        if (field?.options_source_config && typeof field.options_source_config === "object") {
                            payload.options_source_config = deepClone(field.options_source_config);
                        }
                        if (field?.rows) payload.rows = field.rows;
                        if (field?.min !== undefined && field?.min !== null) payload.min = field.min;
                        if (field?.max !== undefined && field?.max !== null) payload.max = field.max;
                        if (field?.step !== undefined && field?.step !== null) payload.step = field.step;
                        if (field?.accept) payload.accept = field.accept;
                        if (field?.multiple) payload.multiple = true;
                        if (field?.css_text) payload.css_text = field.css_text;
                        if (field?.js_text) payload.js_text = field.js_text;
                        if (Array.isArray(field?.options || field?.choices || field?.enum)) {
                            payload.options = (field.options || field.choices || field.enum)
                                .map((option) => {
                                    const label = typeof option === "object"
                                        ? (option.label ?? option.name ?? String(option.value ?? option.id ?? "")).toString().trim()
                                        : String(option ?? "").trim();
                                    const value = typeof option === "object"
                                        ? (option.value ?? option.id ?? option.label ?? option.name ?? "")
                                        : option;
                                    if (!label || value === "" || value === undefined || value === null) {
                                        return null;
                                    }
                                    return { label, value };
                                })
                                .filter(Boolean);
                        }
                        return payload;
                    })
                    .filter(Boolean)
                    .sort((a, b) => (a.order || 0) - (b.order || 0));
            };

            const normalizeFormLibrary = (rawLibrary) => {
                const raw = Array.isArray(rawLibrary) ? rawLibrary : [];
                const existed = new Set();
                const normalized = [];
                raw.forEach((item, index) => {
                    if (!item || typeof item !== "object") return;
                    const code = (item.code || "").toString().trim();
                    if (!code || existed.has(code)) return;
                    existed.add(code);
                    normalized.push({
                        code,
                        name: (item.name || code).toString().trim(),
                        description: (item.description || "").toString().trim(),
                        order: Number.isFinite(Number(item.order)) ? Number(item.order) : index,
                        fields: normalizeLibraryFields(item.fields),
                    });
                });
                normalized.sort((a, b) => (a.order || 0) - (b.order || 0));
                normalized.forEach((item, idx) => {
                    item.order = idx;
                });
                return normalized;
            };

            const findLibraryForm = (code) => {
                if (!code) return null;
                const source = globalFormLibrary.length ? globalFormLibrary : formLibrary;
                return source.find((item) => item.code === code) || null;
            };

            const nextFormFieldId = () => {
                const id = `field_${formFieldSeed}`;
                formFieldSeed += 1;
                return id;
            };

            const nextFormOptionId = () => {
                const id = `option_${formFieldSeed}`;
                formFieldSeed += 1;
                return id;
            };

            const defaultFieldLabelMap = {
                input: "单行输入",
                textarea: "多行文本",
                number: "数字",
                file: "文件上传",
                signature: "手写签名",
                radio: "单选",
                checkbox: "多选",
                select: "下拉选择",
                switch: "开关",
                date: "日期",
                datetime: "日期时间",
            };

            const createEmptyFieldOption = () => ({
                id: nextFormOptionId(),
                label: "",
                value: "",
            });

            const getDefaultFieldDataSources = (field) => getAvailableFieldDataSources(
                fieldDataSourceMetadata,
                "default",
                field?.component,
            );

            const getOptionsFieldDataSources = (field) => getAvailableFieldDataSources(
                fieldDataSourceMetadata,
                "options",
                field?.component,
            );

            const getSourceParamsSchema = (field, target) => {
                const ui = target === "default" ? field?.default_source_ui : field?.options_source_ui;
                return getFieldSourceParamSchema(fieldDataSourceMetadata, ui?.source_key, target);
            };

            const onFieldDataSourceChange = (field, target) => {
                const ui = target === "default" ? field?.default_source_ui : field?.options_source_ui;
                if (!ui) return;
                ui.source_params = syncFieldSourceParamsBySchema(
                    fieldDataSourceMetadata,
                    ui.source_key,
                    target,
                    ui.source_params,
                );
            };

            const fieldDataSourcePicker = reactive({
                visible: false,
                keyword: "",
                target: "default",
                fieldId: "",
                fieldRef: null,
                title: "选择数据源类",
                selectedKey: "",
                page: 1,
                pageSize: 8,
                options: [],
            });

            const getFieldDataSourcePickerField = () => {
                if (fieldDataSourcePicker.fieldRef && typeof fieldDataSourcePicker.fieldRef === "object") {
                    return fieldDataSourcePicker.fieldRef;
                }
                const fields = nodeDialog.form.form_fields || [];
                return fields.find((item) => item.id === fieldDataSourcePicker.fieldId) || null;
            };

            const getFieldDataSourceKeyLabel = (key, target, field) => {
                const cleanKey = String(key || "").trim().toLowerCase();
                if (!cleanKey) return "";
                const list = target === "default"
                    ? getDefaultFieldDataSources(field)
                    : getOptionsFieldDataSources(field);
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

            const openFieldDataSourcePicker = (field, target) => {
                if (!field) return;
                fieldDataSourcePicker.visible = true;
                fieldDataSourcePicker.keyword = "";
                fieldDataSourcePicker.target = target;
                fieldDataSourcePicker.fieldId = field.id || "";
                fieldDataSourcePicker.fieldRef = field;
                const filteredList = target === "default"
                    ? getDefaultFieldDataSources(field)
                    : getOptionsFieldDataSources(field);
                const baseList = target === "default"
                    ? getAvailableFieldDataSources(fieldDataSourceMetadata, "default", "")
                    : getAvailableFieldDataSources(fieldDataSourceMetadata, "options", "");
                fieldDataSourcePicker.options = filteredList.length ? filteredList : baseList;
                fieldDataSourcePicker.selectedKey = String(
                    (target === "default" ? field?.default_source_ui?.source_key : field?.options_source_ui?.source_key) || ""
                ).trim().toLowerCase();
                fieldDataSourcePicker.page = 1;
                fieldDataSourcePicker.title = target === "default"
                    ? "选择默认值数据源类"
                    : "选择选项数据源类";
            };

            const closeFieldDataSourcePicker = () => {
                fieldDataSourcePicker.visible = false;
                fieldDataSourcePicker.keyword = "";
                fieldDataSourcePicker.fieldId = "";
                fieldDataSourcePicker.fieldRef = null;
                fieldDataSourcePicker.selectedKey = "";
                fieldDataSourcePicker.page = 1;
                fieldDataSourcePicker.options = [];
            };

            const chooseFieldDataSource = (item) => {
                if (!item) return;
                fieldDataSourcePicker.selectedKey = item.key;
            };

            const applyFieldDataSourceSelection = () => {
                const field = getFieldDataSourcePickerField();
                if (!field) return;
                const ui = fieldDataSourcePicker.target === "default"
                    ? field.default_source_ui
                    : field.options_source_ui;
                if (!ui) return;
                ui.source_key = String(fieldDataSourcePicker.selectedKey || "").trim().toLowerCase();
                onFieldDataSourceChange(field, fieldDataSourcePicker.target);
                closeFieldDataSourcePicker();
            };

            const clearFieldDataSourceSelection = () => {
                fieldDataSourcePicker.selectedKey = "";
            };

            const onFieldDataSourcePickerKeywordChange = () => {
                fieldDataSourcePicker.page = 1;
            };

            const usesManualOptions = (field) => shouldUseManualOptions(field);

            const createEmptyFormField = (component = "input") => ({
                id: nextFormFieldId(),
                key: "",
                label: defaultFieldLabelMap[component] || "新字段",
                component,
                placeholder: "",
                default: component === "switch" ? false : "",
                required: false,
                rows: component === "textarea" ? 3 : undefined,
                min: undefined,
                max: undefined,
                step: component === "number" ? 1 : undefined,
                accept: component === "file" ? "" : undefined,
                multiple: component === "file" ? false : undefined,
                css_text: "",
                js_text: "",
                default_source_ui: {
                    mode: "fixed",
                    source_key: "",
                    source_params: {},
                    fallback_value: "",
                    legacy_config: null,
                },
                context_binding: {
                    write_target: "node",
                    write_mode: "overwrite",
                },
                options_source_ui: {
                    mode: "manual",
                    source_key: "",
                    source_params: {},
                    fallback_to_manual: true,
                    legacy_config: null,
                },
                options: ["select", "radio", "checkbox"].includes(component) ? [createEmptyFieldOption()] : [],
            });

            const normalizeFormSchemaFields = (schema) => {
                const rawFields = Array.isArray(schema)
                    ? schema
                    : Array.isArray(schema?.fields)
                        ? schema.fields
                        : [];
                return rawFields.map((field) => ({
                    ...(field || {}),
                    id: nextFormFieldId(),
                    key: field?.key || field?.name || field?.prop || "",
                    label: field?.label || field?.title || field?.name || "",
                    component: field?.component || field?.widget || field?.type || "input",
                    placeholder: field?.placeholder || "",
                    default: Object.prototype.hasOwnProperty.call(field || {}, "default")
                        ? field.default
                        : field?.default_value ?? "",
                    required: !!field?.required,
                    rows: field?.rows,
                    min: field?.min,
                    max: field?.max,
                    step: field?.step,
                    accept: field?.accept,
                    multiple: !!field?.multiple,
                    css_text: field?.css_text || "",
                    js_text: field?.js_text || "",
                    default_source_ui: normalizeDefaultSourceUi(
                        field,
                        Object.prototype.hasOwnProperty.call(field || {}, "default")
                            ? field.default
                            : field?.default_value ?? ""
                    ),
                    context_binding: normalizeContextBindingUi(field),
                    options_source_ui: normalizeOptionsSourceUi(field),
                    options: Array.isArray(field?.options || field?.choices || field?.enum)
                        ? (field.options || field.choices || field.enum).map((option) => ({
                            id: nextFormOptionId(),
                            label: typeof option === "object" ? option.label ?? option.name ?? String(option.value ?? option.id ?? "") : String(option ?? ""),
                            value: typeof option === "object" ? option.value ?? option.id ?? option.label ?? option.name ?? "" : option,
                        }))
                        : [],
                }));
            };

            const buildFormSchemaFromFields = (fields) => {
                const normalizedFields = (fields || [])
                    .map((field, index) => {
                        const key = (field.key || "").trim();
                        const label = (field.label || "").trim();
                        if (!key || !label) return null;
                        const payload = {
                            key,
                            label,
                            component: field.component || "input",
                            required: !!field.required,
                        };
                        if (field.placeholder) payload.placeholder = field.placeholder;
                        if (
                            (field?.default_source_ui?.mode || "fixed") === "fixed"
                            && field.default !== ""
                            && field.default !== undefined
                            && field.default !== null
                        ) payload.default = field.default;
                        Object.assign(payload, buildDefaultSourcePayload(field));
                        if (field.component === "textarea" && field.rows) payload.rows = field.rows;
                        if (field.component === "file") {
                            if (field.accept) payload.accept = field.accept;
                            if (field.multiple) payload.multiple = true;
                        }
                        if (field.css_text) payload.css_text = field.css_text;
                        if (field.js_text) payload.js_text = field.js_text;
                        if (field.component === "number") {
                            if (field.min !== undefined && field.min !== null) payload.min = field.min;
                            if (field.max !== undefined && field.max !== null) payload.max = field.max;
                            if (field.step !== undefined && field.step !== null) payload.step = field.step;
                        }
                        if (["select", "radio", "checkbox"].includes(field.component)) {
                            const options = (field.options || [])
                                .map((option) => {
                                    const labelVal = (option.label ?? "").toString().trim();
                                    const valueVal = option.value;
                                    if (!labelVal || valueVal === "" || valueVal === undefined || valueVal === null) {
                                        return null;
                                    }
                                    return {
                                        label: labelVal,
                                        value: valueVal,
                                    };
                                })
                                .filter(Boolean);
                            if (usesManualOptions(field)) {
                                payload.options = options;
                            }
                            Object.assign(payload, buildOptionsSourcePayload(field));
                        }
                        Object.assign(payload, buildContextBindingPayload(field));
                        payload.order = index;
                        return payload;
                    })
                    .filter(Boolean);
                return normalizedFields.length ? { fields: normalizedFields } : null;
            };

            const ensureNodePosition = (node, index) => {
                if (typeof node.x === "number" && typeof node.y === "number") return;
                const col = index % 4;
                const row = Math.floor(index / 4);
                node.x = 80 + col * 280;
                node.y = 80 + row * 180;
            };

            const loadDetail = async () => {
                if (!flowId.value) return;
                const res = await request.get("/flow_engine/flow_definition_detail", { flow_id: flowId.value });
                flowForm.code = res.code;
                flowForm.name = res.name;
                flowForm.description = res.description;
                flowForm.is_active = res.is_active;
                const normalizedLibrary = normalizeFormLibrary(res.form_library || []);
                formLibrary.splice(0, formLibrary.length, ...normalizedLibrary);

                const mappedNodes = (res.nodes || []).map((n, index) => {
                    const ui = (n.form_schema && n.form_schema.__ui) || {};
                    const cleanedSchema = stripUi(n.form_schema);
                    const formRefCode = (cleanedSchema && cleanedSchema[FORM_REF_CODE_KEY]) || "";
                    const node = {
                        ...n,
                        x: typeof ui.x === "number" ? ui.x : undefined,
                        y: typeof ui.y === "number" ? ui.y : undefined,
                        form_schema: cleanedSchema,
                        form_schema_text: cleanedSchema ? JSON.stringify(cleanedSchema, null, 2) : "",
                        form_ref_code: formRefCode,
                    };
                    ensureNodePosition(node, index);
                    return node;
                });
                nodes.splice(0, nodes.length, ...mappedNodes);
                transitions.splice(0, transitions.length, ...(res.transitions || []));
            };

            const loadGlobalFormLibrary = async () => {
                const res = await request.get("/flow_engine/form_library_global_list");
                const normalized = normalizeFormLibrary(res || []);
                globalFormLibrary.splice(0, globalFormLibrary.length, ...normalized);
            };

            const refreshFormLibrary = async () => {
                await loadGlobalFormLibrary();
                ElMessage.success("表单库已刷新");
            };

            const nextCode = (prefix) => {
                const existed = new Set(nodes.map((n) => n.code));
                let idx = 1;
                while (true) {
                    const code = `${prefix}_${idx}`;
                    if (!existed.has(code)) return code;
                    idx += 1;
                }
            };

            const addNodeFromPalette = (nodeType) => {
                const typePrefixMap = {
                    start: "start",
                    task: "task",
                    condition: "cond",
                    end: "end",
                };
                const prefix = typePrefixMap[nodeType] || "node";
                const code = nextCode(prefix);
                const newNode = {
                    code,
                    name: `新${nodeTypeLabel(nodeType)}`,
                    node_type: nodeType,
                    approval_mode: "any",
                    is_auto: false,
                    order: nodes.length,
                    x: 180 + (nodes.length % 4) * 260,
                    y: 120 + Math.floor(nodes.length / 4) * 170,
                    form_schema: null,
                    form_schema_text: "",
                    form_ref_code: "",
                    groups: [],
                };
                nodes.push(newNode);
                selectedNodeIndex.value = nodes.length - 1;
                selectedEdgeIndex.value = -1;
            };

            const autoLayout = () => {
                nodes.forEach((node, i) => {
                    const col = i % 4;
                    const row = Math.floor(i / 4);
                    node.x = 80 + col * 280;
                    node.y = 80 + row * 190;
                });
            };

            const clearSelection = () => {
                selectedNodeIndex.value = -1;
                selectedEdgeIndex.value = -1;
                connectState.fromIndex = -1;
                hoveredEdgeIndex.value = -1;
            };

            const createEdgeIfNeeded = (fromIndex, toIndex) => {
                const fromNode = nodes[fromIndex];
                const toNode = nodes[toIndex];
                if (!fromNode || !toNode) return false;
                if (fromNode.code === toNode.code) return false;
                const duplicated = transitions.some(
                    (t) => t.source_code === fromNode.code && t.target_code === toNode.code
                );
                if (duplicated) return false;
                transitions.push({
                    source_code: fromNode.code,
                    target_code: toNode.code,
                    condition_expr: "",
                    description: "",
                });
                return true;
            };

            const selectNode = (index) => {
                selectedNodeIndex.value = index;
                selectedEdgeIndex.value = -1;
            };

            const selectEdge = (index) => {
                selectedEdgeIndex.value = index;
                selectedNodeIndex.value = -1;
            };

            const nodeCenter = (node, side) => {
                if (!node) return null;
                const nodeEl = nodeRefMap.get(node);
                const nodeHeight = nodeEl ? nodeEl.offsetHeight : NODE_HEIGHT;
                const y = node.y + nodeHeight / 2;
                if (side === "out") {
                    return { x: node.x + NODE_WIDTH, y };
                }
                return { x: node.x, y };
            };

            const getNodeByCode = (code) => nodes.find((n) => n.code === code);

            const edgePathByPoints = (sourcePoint, targetPoint) => {
                if (!sourcePoint || !targetPoint) return "";
                const cp1x = sourcePoint.x + 60;
                const cp2x = targetPoint.x - 60;
                return `M ${sourcePoint.x} ${sourcePoint.y} C ${cp1x} ${sourcePoint.y}, ${cp2x} ${targetPoint.y}, ${targetPoint.x} ${targetPoint.y}`;
            };

            const getEdgePath = (edge) => {
                const sourceNode = getNodeByCode(edge.source_code);
                const targetNode = getNodeByCode(edge.target_code);
                if (!sourceNode || !targetNode) return "";
                return edgePathByPoints(nodeCenter(sourceNode, "out"), nodeCenter(targetNode, "in"));
            };

            const getEdgeDeletePoint = (edge) => {
                const sourceNode = getNodeByCode(edge.source_code);
                const targetNode = getNodeByCode(edge.target_code);
                if (!sourceNode || !targetNode) return null;
                const sourcePoint = nodeCenter(sourceNode, "out");
                const targetPoint = nodeCenter(targetNode, "in");
                if (!sourcePoint || !targetPoint) return null;
                const cp1 = { x: sourcePoint.x + 60, y: sourcePoint.y };
                const cp2 = { x: targetPoint.x - 60, y: targetPoint.y };
                const t = 0.5;
                const mt = 1 - t;
                const x = (mt ** 3) * sourcePoint.x + 3 * (mt ** 2) * t * cp1.x + 3 * mt * (t ** 2) * cp2.x + (t ** 3) * targetPoint.x;
                const y = (mt ** 3) * sourcePoint.y + 3 * (mt ** 2) * t * cp1.y + 3 * mt * (t ** 2) * cp2.y + (t ** 3) * targetPoint.y;
                return { x, y };
            };

            const previewPath = computed(() => {
                if (connectState.fromIndex < 0) return "";
                const sourceNode = nodes[connectState.fromIndex];
                if (!sourceNode) return "";
                const sourcePoint = nodeCenter(sourceNode, "out");
                if (!canvasWrapRef.value) return "";
                const targetPoint = {
                    x: connectState.mouseX,
                    y: connectState.mouseY,
                };
                return edgePathByPoints(sourcePoint, targetPoint);
            });

            const toggleConnectMode = () => {
                connectMode.value = !connectMode.value;
                connectState.fromIndex = -1;
            };

            const onSourceHandleClick = (index) => {
                if (!connectMode.value) {
                    connectMode.value = true;
                }
                connectState.fromIndex = index;
            };
            const onTargetHandleClick = (index) => {
                if (connectState.fromIndex < 0) return;
                const ok = createEdgeIfNeeded(connectState.fromIndex, index);
                connectState.fromIndex = -1;
                if (ok) {
                    selectedEdgeIndex.value = transitions.length - 1;
                    selectedNodeIndex.value = -1;
                }
            };

            const removeTransition = (index) => {
                if (index < 0) return;
                transitions.splice(index, 1);
                selectedEdgeIndex.value = -1;
                hoveredEdgeIndex.value = -1;
            };

            const removeNode = (index) => {
                if (index < 0 || index >= nodes.length) return;
                const removed = nodes[index];
                nodes.splice(index, 1);
                for (let i = transitions.length - 1; i >= 0; i -= 1) {
                    if (
                        transitions[i].source_code === removed.code ||
                        transitions[i].target_code === removed.code
                    ) {
                        transitions.splice(i, 1);
                    }
                }
                selectedNodeIndex.value = -1;
                selectedEdgeIndex.value = -1;
            };

            const startDragNode = (index, evt) => {
                const node = nodes[index];
                if (!node || !canvasWrapRef.value) return;
                const rect = canvasWrapRef.value.getBoundingClientRect();
                dragState.active = true;
                dragState.nodeIndex = index;
                dragState.offsetX = evt.clientX - rect.left - node.x + canvasWrapRef.value.scrollLeft;
                dragState.offsetY = evt.clientY - rect.top - node.y + canvasWrapRef.value.scrollTop;
            };

            const onMouseMove = (evt) => {
                if (connectMode.value && canvasWrapRef.value) {
                    const rect = canvasWrapRef.value.getBoundingClientRect();
                    connectState.mouseX = evt.clientX - rect.left + canvasWrapRef.value.scrollLeft;
                    connectState.mouseY = evt.clientY - rect.top + canvasWrapRef.value.scrollTop;
                }

                if (!dragState.active || dragState.nodeIndex < 0 || !canvasWrapRef.value) return;
                const node = nodes[dragState.nodeIndex];
                if (!node) return;
                const rect = canvasWrapRef.value.getBoundingClientRect();
                const x = evt.clientX - rect.left + canvasWrapRef.value.scrollLeft - dragState.offsetX;
                const y = evt.clientY - rect.top + canvasWrapRef.value.scrollTop - dragState.offsetY;
                node.x = Math.max(20, Math.min(2140, Math.round(x)));
                node.y = Math.max(20, Math.min(1280, Math.round(y)));
            };

            const onMouseUp = () => {
                dragState.active = false;
                dragState.nodeIndex = -1;
            };

            const applyRefSchemaMeta = (schema, formRefCode) => {
                if (!schema || typeof schema !== "object") {
                    schema = {};
                }
                if (!formRefCode) {
                    delete schema[FORM_REF_CODE_KEY];
                    delete schema[FORM_REF_NAME_KEY];
                    return schema;
                }
                const matched = findLibraryForm(formRefCode);
                if (!matched) {
                    delete schema[FORM_REF_CODE_KEY];
                    delete schema[FORM_REF_NAME_KEY];
                    return schema;
                }
                schema[FORM_REF_CODE_KEY] = matched.code;
                schema[FORM_REF_NAME_KEY] = matched.name;
                return schema;
            };

            const onNodeFormRefChange = (formRefCode) => {
                if (!formRefCode) {
                    nodeDialog.form.form_ref_code = "";
                    const schema = applyRefSchemaMeta(
                        nodeDialog.form.form_schema ? deepClone(nodeDialog.form.form_schema) : {},
                        ""
                    );
                    nodeDialog.form.form_schema = Object.keys(schema).length ? schema : null;
                    nodeDialog.form.form_schema_text = nodeDialog.form.form_schema
                        ? JSON.stringify(nodeDialog.form.form_schema, null, 2)
                        : "";
                    return;
                }
                const matched = findLibraryForm(formRefCode);
                if (!matched) {
                    ElMessage.error(`未找到表单库定义: ${formRefCode}`);
                    nodeDialog.form.form_ref_code = "";
                    return;
                }
                nodeDialog.form.form_ref_code = formRefCode;
                nodeDialog.form.legacy_form_schema = null;
                nodeDialog.form.form_fields = normalizeFormSchemaFields({
                    fields: deepClone(matched.fields || []),
                });
                const schema = applyRefSchemaMeta({
                    fields: deepClone(matched.fields || []),
                }, formRefCode);
                nodeDialog.form.form_schema = schema;
                nodeDialog.form.form_schema_text = JSON.stringify(schema, null, 2);
            };

            const openNodeDialog = (index = -1) => {
                nodeDialog.editIndex = index;
                nodeDialog.dragIndex = -1;
                if (index >= 0) {
                    nodeDialog.form = deepClone(nodes[index]);
                    const refCode = (nodeDialog.form.form_schema && nodeDialog.form.form_schema[FORM_REF_CODE_KEY])
                        || nodeDialog.form.form_ref_code
                        || "";
                    nodeDialog.form.form_ref_code = refCode;
                    if (refCode) {
                        onNodeFormRefChange(refCode);
                    } else {
                        nodeDialog.form.form_fields = normalizeFormSchemaFields(nodeDialog.form.form_schema);
                        nodeDialog.form.legacy_form_schema = nodeDialog.form.form_fields.length
                            ? null
                            : (nodeDialog.form.form_schema ? deepClone(nodeDialog.form.form_schema) : null);
                        nodeDialog.form.form_schema_text = nodeDialog.form.form_schema
                            ? JSON.stringify(nodeDialog.form.form_schema, null, 2)
                            : "";
                    }
                } else {
                    nodeDialog.form = {
                        code: nextCode("task"),
                        name: "新任务",
                        node_type: "task",
                        approval_mode: "any",
                        is_auto: false,
                        order: nodes.length,
                        x: 100,
                        y: 100,
                        form_schema_text: "",
                        form_schema: null,
                        form_ref_code: "",
                        form_fields: [],
                        legacy_form_schema: null,
                        groups: [],
                    };
                }
                nodeDialog.visible = true;
            };

            const addFormField = (component = "input") => {
                if (nodeDialog.form.form_ref_code) return;
                nodeDialog.form.legacy_form_schema = null;
                nodeDialog.form.form_fields.push(createEmptyFormField(component));
            };

            const removeFormField = (index) => {
                if (nodeDialog.form.form_ref_code) return;
                nodeDialog.form.form_fields.splice(index, 1);
            };

            const addFormFieldOption = (field) => {
                if (nodeDialog.form.form_ref_code) return;
                if (!Array.isArray(field.options)) {
                    field.options = [];
                }
                field.options.push(createEmptyFieldOption());
            };

            const removeFormFieldOption = (field, optionIndex) => {
                if (nodeDialog.form.form_ref_code) return;
                if (!Array.isArray(field.options)) return;
                field.options.splice(optionIndex, 1);
            };

            const onFormFieldDragStart = (index) => {
                if (nodeDialog.form.form_ref_code) return;
                nodeDialog.dragIndex = index;
            };

            const onFormFieldDrop = (index) => {
                const fromIndex = nodeDialog.dragIndex;
                nodeDialog.dragIndex = -1;
                if (fromIndex < 0 || fromIndex === index) return;
                const moved = nodeDialog.form.form_fields.splice(fromIndex, 1)[0];
                if (!moved) return;
                nodeDialog.form.form_fields.splice(index, 0, moved);
            };

            const onFormFieldDragEnd = () => {
                nodeDialog.dragIndex = -1;
            };

            const addGroup = () => {
                nodeDialog.form.groups.push({
                    key: "",
                    name: "",
                    min_approve_count: 1,
                    order: nodeDialog.form.groups.length,
                    rules: [],
                });
            };

            const removeGroup = (index) => {
                nodeDialog.form.groups.splice(index, 1);
            };

            const addRule = (groupIndex) => {
                nodeDialog.form.groups[groupIndex].rules.push({
                    rule_type: "perm_pack",
                    perm_pack_id: null,
                    user_id: null,
                });
            };

            const removeRule = (groupIndex, ruleIndex) => {
                nodeDialog.form.groups[groupIndex].rules.splice(ruleIndex, 1);
            };

            const confirmNode = () => {
                let formFields = nodeDialog.form.form_fields || [];
                if (nodeDialog.form.form_ref_code) {
                    const matched = findLibraryForm(nodeDialog.form.form_ref_code);
                    if (!matched) {
                        ElMessage.error(`引用表单不存在: ${nodeDialog.form.form_ref_code}`);
                        return;
                    }
                    formFields = normalizeFormSchemaFields({
                        fields: deepClone(matched.fields || []),
                    });
                    nodeDialog.form.form_fields = formFields;
                }
                const duplicateKeys = new Set();
                for (const field of formFields) {
                    const key = (field.key || "").trim();
                    const label = (field.label || "").trim();
                    if (!key && !label) {
                        continue;
                    }
                    if (!key || !label) {
                        ElMessage.error("节点表单中的字段标识和字段名称都不能为空");
                        return;
                    }
                    if (duplicateKeys.has(key)) {
                        ElMessage.error(`节点表单字段标识重复: ${key}`);
                        return;
                    }
                    duplicateKeys.add(key);
                    const needsManualOptions = usesManualOptions(field);
                    if (["select", "radio", "checkbox"].includes(field.component) && needsManualOptions && !(field.options || []).length) {
                        ElMessage.error(`字段[${label}]至少需要一个选项`);
                        return;
                    }
                }
                let formSchema = nodeDialog.form.form_ref_code
                    ? { fields: deepClone(findLibraryForm(nodeDialog.form.form_ref_code)?.fields || []) }
                    : (formFields.length
                        ? buildFormSchemaFromFields(formFields)
                        : nodeDialog.form.legacy_form_schema);
                if (formSchema && typeof formSchema === "object") {
                    formSchema = applyRefSchemaMeta(
                        deepClone(formSchema),
                        nodeDialog.form.form_ref_code || ""
                    );
                }
                const payloadNode = {
                    ...deepClone(nodeDialog.form),
                    form_schema: formSchema,
                    form_schema_text: formSchema ? JSON.stringify(formSchema, null, 2) : "",
                };
                if (nodeDialog.editIndex >= 0) {
                    nodes[nodeDialog.editIndex] = payloadNode;
                    selectedNodeIndex.value = nodeDialog.editIndex;
                } else {
                    nodes.push(payloadNode);
                    selectedNodeIndex.value = nodes.length - 1;
                }
                selectedEdgeIndex.value = -1;
                nodeDialog.visible = false;
            };

            const validateBeforeSave = () => {
                if (!nodes.length) {
                    ElMessage.error("至少需要一个节点");
                    return false;
                }
                const startNodes = nodes.filter((n) => n.node_type === "start");
                if (startNodes.length !== 1) {
                    ElMessage.error("必须且只能有一个开始节点");
                    return false;
                }
                const codeSet = new Set();
                for (const node of nodes) {
                    if (!node.code) {
                        ElMessage.error("节点编码不能为空");
                        return false;
                    }
                    if (codeSet.has(node.code)) {
                        ElMessage.error(`节点编码重复: ${node.code}`);
                        return false;
                    }
                    codeSet.add(node.code);
                }
                return true;
            };

            const saveFlow = async (options = {}) => {
                const showMessage = typeof options.showMessage === "boolean" ? options.showMessage : true;
                const allowWhilePublishing = !!options.allowWhilePublishing;
                if (pageData.saving || (!allowWhilePublishing && pageData.publishing)) return false;
                if (!validateBeforeSave()) return false;
                if (!flowFormRef.value) return false;
                pageData.saving = true;
                try {
                    await nextTick();
                    const valid = await flowFormRef.value.validate().catch(() => false);
                    if (!valid) return false;

                    const payloadNodes = [];
                    for (let idx = 0; idx < nodes.length; idx += 1) {
                        const node = nodes[idx];
                        let parsedSchema = null;
                        if (node.form_schema_text) {
                            try {
                                parsedSchema = JSON.parse(node.form_schema_text);
                            } catch (err) {
                                ElMessage.error(`节点[${node.code}]表单配置不是合法 JSON`);
                                return false;
                            }
                        } else if (node.form_schema) {
                            parsedSchema = deepClone(node.form_schema);
                        }
                        if (node.form_ref_code) {
                            const matched = findLibraryForm(node.form_ref_code);
                            if (!matched) {
                                ElMessage.error(`节点[${node.code}]引用表单不存在: ${node.form_ref_code}`);
                                return false;
                            }
                            parsedSchema = applyRefSchemaMeta({
                                fields: deepClone(matched.fields || []),
                            }, node.form_ref_code);
                        }
                        const mergedSchema = parsedSchema || {};
                        mergedSchema.__ui = { x: node.x, y: node.y };
                        payloadNodes.push({
                            code: node.code,
                            name: node.name,
                            node_type: node.node_type,
                            approval_mode: node.approval_mode,
                            is_auto: node.is_auto,
                            order: idx,
                            form_schema: mergedSchema,
                            groups: (node.groups || []).map((g, gIdx) => ({
                                key: g.key,
                                name: g.name,
                                min_approve_count: g.min_approve_count,
                                order: g.order ?? gIdx,
                                rules: (g.rules || []).map((r) => ({
                                    rule_type: r.rule_type,
                                    perm_pack_id: r.perm_pack_id,
                                    user_id: r.user_id,
                                })),
                            })),
                        });
                    }

                    const payload = {
                        flow_id: flowId.value || null,
                        code: flowForm.code,
                        name: flowForm.name,
                        description: flowForm.description,
                        is_active: flowForm.is_active,
                        nodes: payloadNodes,
                        transitions: transitions.map((t) => ({
                            source_code: t.source_code,
                            target_code: t.target_code,
                            condition_expr: t.condition_expr,
                            description: t.description,
                        })),
                        form_library: [],
                    };

                    const res = await request.post("/flow_engine/flow_definition_save", payload);
                    if (res && res.flow_id) {
                        flowId.value = String(res.flow_id);
                    }
                    if (showMessage) {
                        ElMessage.success("保存成功");
                    }
                    return true;
                } finally {
                    pageData.saving = false;
                }
            };

            const publishFlow = async () => {
                if (pageData.saving || pageData.publishing) return;
                pageData.publishing = true;
                try {
                    await nextTick();
                    const saved = await saveFlow({ showMessage: false, allowWhilePublishing: true });
                    if (!saved || !flowId.value) {
                        return;
                    }
                    await request.post("/flow_engine/flow_definition_publish", {
                        flow_id: Number(flowId.value),
                    });
                    ElMessage.success("发布成功");
                } finally {
                    pageData.publishing = false;
                }
            };

            const exportFlowJson = async () => {
                if (!flowId.value) {
                    ElMessage.warning("请先保存流程");
                    return;
                }
                const res = await request.get("/flow_engine/flow_definition_export", {
                    flow_id: Number(flowId.value),
                });
                const text = JSON.stringify(res, null, 2);
                const blob = new Blob([text], { type: "application/json;charset=utf-8" });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${res.code || flowForm.code || "flow_definition"}.json`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            };

            const openImportDialog = () => {
                importDialog.visible = true;
                importDialog.overwrite = false;
                importDialog.text = "";
            };

            const triggerImportFile = () => {
                if (importFileRef.value) {
                    importFileRef.value.click();
                }
            };

            const onImportFileChange = async (evt) => {
                const file = evt.target.files && evt.target.files[0];
                if (!file) return;
                try {
                    importDialog.text = await file.text();
                } finally {
                    evt.target.value = "";
                }
            };

            const confirmImportJson = async () => {
                if (!importDialog.text.trim()) {
                    ElMessage.warning("请先粘贴 JSON 或选择文件");
                    return;
                }
                let parsed = null;
                try {
                    parsed = JSON.parse(importDialog.text);
                } catch (err) {
                    ElMessage.error("JSON 格式不合法");
                    return;
                }
                const res = await request.post("/flow_engine/flow_definition_import", {
                    overwrite: importDialog.overwrite,
                    payload: parsed,
                });
                if (res && res.flow_id) {
                    flowId.value = String(res.flow_id);
                }
                await loadDetail();
                importDialog.visible = false;
                ElMessage.success("导入成功");
            };

            onMounted(async () => {
                window.addEventListener("mousemove", onMouseMove);
                window.addEventListener("mouseup", onMouseUp);
                await loadOptions();
                await loadDetail();
                await loadGlobalFormLibrary();
                pageData.pageLoading = false;
            });

            onBeforeUnmount(() => {
                window.removeEventListener("mousemove", onMouseMove);
                window.removeEventListener("mouseup", onMouseUp);
            });

            return {
                goBack,
                flowId,
                pageData,
                flowFormRef,
                flowForm,
                flowRules,
                formLibraryOptions,
                currentNodeFormRefName,
                canvasWrapRef,
                canvasBoardRef,
                importFileRef,
                importDialog,
                nodes,
                transitions,
                nodeTypeOptions,
                approvalModeOptions,
                ruleTypeOptions,
                nodeDialog,
                permPackOptions,
                userOptions,
                userLoading,
                connectMode,
                connectState,
                selectedNodeIndex,
                selectedEdgeIndex,
                hoveredEdgeIndex,
                selectedNode,
                selectedEdge,
                previewPath,
                nodeTypeLabel,
                formatUserLabel,
                searchUsers,
                addNodeFromPalette,
                autoLayout,
                clearSelection,
                selectNode,
                selectEdge,
                setNodeRef,
                getEdgePath,
                getEdgeDeletePoint,
                toggleConnectMode,
                onSourceHandleClick,
                onTargetHandleClick,
                removeNode,
                removeTransition,
                startDragNode,
                openNodeDialog,
                addFormField,
                removeFormField,
                addFormFieldOption,
                removeFormFieldOption,
                fieldDataSourceMetadata,
                getDefaultFieldDataSources,
                getOptionsFieldDataSources,
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
                onFieldDataSourcePickerKeywordChange,
                buildFieldDataSourcePlaceholder,
                usesManualOptions,
                onFormFieldDragStart,
                onFormFieldDrop,
                onFormFieldDragEnd,
                onNodeFormRefChange,
                addGroup,
                removeGroup,
                addRule,
                removeRule,
                confirmNode,
                refreshFormLibrary,
                saveFlow,
                publishFlow,
                exportFlowJson,
                openImportDialog,
                triggerImportFile,
                onImportFileChange,
                confirmImportJson,
            };
        },
    });
}
