import { createSignatureFieldComponent } from "./signature_field.js";

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
    const HISTORY_LIMIT = 80;
    const DRAFT_STORAGE_PREFIX = "flow_form_designer_draft";
    const PLACEHOLDER_COMPONENTS = new Set(["placeholder"]);
    const TEXT_COMPONENTS = new Set(["title_h1", "title_h2", "title_h3", "title_h4", "title_h5", "paragraph"]);
    const VARIABLE_COMPONENTS = new Set(["var_username", "var_phone", "var_full_name"]);
    const DISPLAY_COMPONENTS = new Set([...PLACEHOLDER_COMPONENTS, ...TEXT_COMPONENTS, ...VARIABLE_COMPONENTS]);
    const VARIABLE_META_MAP = {
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
    const buildFieldDataSourcePlaceholder = (target) => target === "default"
        ? "请选择默认值数据源"
        : "请选择选项数据源";

    const resolveVariableValueByKey = (key) => {
        const cleanKey = String(key || "").trim();
        if (!cleanKey) return "";
        return currentUser?.[cleanKey] ?? "";
    };

    const buildTextDisplayStyle = (node) => {
        const align = String(node?.text_align || "left").trim();
        const vertical = String(node?.text_v_align || "top").trim();
        const minHeightRaw = Number(node?.text_min_height);
        const minHeight = Number.isFinite(minHeightRaw) ? Math.max(0, minHeightRaw) : 48;
        const justifyMap = {
            left: "flex-start",
            center: "center",
            right: "flex-end",
        };
        const alignMap = {
            top: "flex-start",
            middle: "center",
            bottom: "flex-end",
        };
        const baseParts = [
            "display:flex",
            "width:100%",
            "box-sizing:border-box",
            `justify-content:${justifyMap[align] || "flex-start"}`,
            `align-items:${alignMap[vertical] || "flex-start"}`,
            `text-align:${align || "left"}`,
            `min-height:${minHeight}px`,
        ];
        const base = baseParts.join(";");
        const custom = String(node?.css_text || "").trim();
        return custom ? `${base};${custom}` : base;
    };

    const SignatureField = createSignatureFieldComponent();

    const ComponentPreview = {
        name: "ComponentPreview",
        props: {
            node: {
                type: Object,
                required: true,
            },
            componentLabel: {
                type: Function,
                required: true,
            },
        },
        methods: {
            resolveVariableValue(node) {
                const fallbackKey = VARIABLE_META_MAP[node?.component]?.key || "";
                const variableKey = String(node?.variable_key || fallbackKey).trim();
                return resolveVariableValueByKey(variableKey);
            },
            withAlignStyle(node) {
                return buildTextDisplayStyle(node);
            },
        },
        template: `
            <div>
                <h1
                    v-if="node.component === 'title_h1'"
                    class="fd-preview-heading fd-preview-h1"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '一级标题' ]]</h1>

                <h2
                    v-else-if="node.component === 'title_h2'"
                    class="fd-preview-heading fd-preview-h2"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '二级标题' ]]</h2>

                <h3
                    v-else-if="node.component === 'title_h3'"
                    class="fd-preview-heading fd-preview-h3"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '三级标题' ]]</h3>

                <h4
                    v-else-if="node.component === 'title_h4'"
                    class="fd-preview-heading fd-preview-h4"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '四级标题' ]]</h4>

                <h5
                    v-else-if="node.component === 'title_h5'"
                    class="fd-preview-heading fd-preview-h5"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '五级标题' ]]</h5>

                <p
                    v-else-if="node.component === 'paragraph'"
                    class="fd-preview-paragraph"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '文本内容' ]]</p>

                <div
                    v-else-if="node.component === 'var_username' || node.component === 'var_phone' || node.component === 'var_full_name'"
                    class="fd-preview-variable"
                    :style="node.css_text || ''">
                    [[ node.variable_label || node.label || componentLabel(node.component) ]]: [[ resolveVariableValue(node) || '-' ]]
                </div>

                <div
                    v-else-if="node.component === 'placeholder'"
                    class="fd-preview-placeholder"
                    :style="node.css_text || ''">
                    [[ node.content || '占位符' ]]
                </div>

                <el-input
                    v-else-if="node.component === 'input'"
                    class="fd-preview-control"
                    :placeholder="node.placeholder || '请输入'"
                    disabled
                    :style="node.css_text || ''"></el-input>

                <el-input
                    v-else-if="node.component === 'textarea'"
                    type="textarea"
                    :rows="node.rows || 3"
                    class="fd-preview-control"
                    :placeholder="node.placeholder || '请输入'"
                    disabled
                    :style="node.css_text || ''"></el-input>

                <el-input-number
                    v-else-if="node.component === 'number'"
                    class="fd-preview-control"
                    :min="node.min"
                    :max="node.max"
                    :step="node.step || 1"
                    disabled
                    style="width: 100%;"
                    :style="node.css_text || ''"></el-input-number>

                <div v-else-if="node.component === 'file'" class="fd-preview-text" :style="node.css_text || ''">
                    文件上传控件
                </div>

                <div v-else-if="node.component === 'signature'" class="fd-preview-text" :style="node.css_text || ''">
                    手写签名控件
                </div>

                <el-radio-group
                    v-else-if="node.component === 'radio'"
                    class="fd-preview-control"
                    disabled
                    :style="node.css_text || ''">
                    <el-radio
                        v-for="(opt, idx) in node.options || []"
                        :key="opt.id || idx"
                        :label="opt.value">[[ opt.label || '选项' ]]</el-radio>
                </el-radio-group>

                <el-checkbox-group
                    v-else-if="node.component === 'checkbox'"
                    class="fd-preview-control"
                    disabled
                    :style="node.css_text || ''">
                    <el-checkbox
                        v-for="(opt, idx) in node.options || []"
                        :key="opt.id || idx"
                        :label="opt.value">[[ opt.label || '选项' ]]</el-checkbox>
                </el-checkbox-group>

                <el-select
                    v-else-if="node.component === 'select'"
                    class="fd-preview-control"
                    :placeholder="node.placeholder || '请选择'"
                    disabled
                    :style="node.css_text || ''">
                    <el-option
                        v-for="(opt, idx) in node.options || []"
                        :key="opt.id || idx"
                        :label="opt.label || '选项'"
                        :value="opt.value"></el-option>
                </el-select>

                <el-switch
                    v-else-if="node.component === 'switch'"
                    disabled
                    :style="node.css_text || ''"></el-switch>

                <el-date-picker
                    v-else-if="node.component === 'date'"
                    class="fd-preview-control"
                    type="date"
                    placeholder="请选择日期"
                    disabled
                    :style="node.css_text || ''"></el-date-picker>

                <el-date-picker
                    v-else-if="node.component === 'datetime'"
                    class="fd-preview-control"
                    type="datetime"
                    placeholder="请选择日期时间"
                    disabled
                    :style="node.css_text || ''"></el-date-picker>

                <div v-else class="fd-preview-text">
                    [[ componentLabel(node.component) ]] 预览
                </div>
            </div>
        `,
    };

    const DesignerNodeItem = {
        name: "DesignerNodeItem",
        components: {
            ComponentPreview,
        },
        props: {
            node: {
                type: Object,
                required: true,
            },
            selectedNodeId: {
                type: String,
                default: "",
            },
            componentLabel: {
                type: Function,
                required: true,
            },
            selectNode: {
                type: Function,
                required: true,
            },
            moveNode: {
                type: Function,
                required: true,
            },
            copyNode: {
                type: Function,
                required: true,
            },
            removeNode: {
                type: Function,
                required: true,
            },
            onNodeDragStart: {
                type: Function,
                required: true,
            },
            onNodeDrop: {
                type: Function,
                required: true,
            },
            onContainerDrop: {
                type: Function,
                required: true,
            },
            onContainerDragOver: {
                type: Function,
                required: true,
            },
            onContainerDragLeave: {
                type: Function,
                required: true,
            },
            isContainerDropActive: {
                type: Function,
                required: true,
            },
            onNodeDragEnter: {
                type: Function,
                required: true,
            },
            isNodeDropTarget: {
                type: Function,
                required: true,
            },
            containerStyle: {
                type: Function,
                required: true,
            },
            childMode: {
                type: Boolean,
                default: false,
            },
        },
        template: `
            <div
                :class="[childMode ? 'fd-child' : 'fd-node', { active: selectedNodeId === node.id, 'fd-drop-before': isNodeDropTarget(node.id) }]"
                draggable="true"
                @dragstart.stop="onNodeDragStart(node.id)"
                @dragenter.stop.prevent="onNodeDragEnter(node.id)"
                @dragover.prevent
                @drop.stop="onNodeDrop(node.id)">
                <div class="fd-node-head" @click.stop="selectNode(node.id)">
                    <div class="fd-node-title">
                        <el-tag size="small">[[ componentLabel(node.component) ]]</el-tag>
                        <span>[[ node.label || node.key || '未命名组件' ]]</span>
                    </div>
                    <div class="fd-node-actions">
                        <el-button link @click.stop="moveNode(node.id, -1)" title="上移"><el-icon><Top /></el-icon></el-button>
                        <el-button link @click.stop="moveNode(node.id, 1)" title="下移"><el-icon><Bottom /></el-icon></el-button>
                        <el-button link @click.stop="copyNode(node.id)" title="复制"><el-icon><CopyDocument /></el-icon></el-button>
                        <el-button link type="danger" @click.stop="removeNode(node.id)" title="删除"><el-icon><Delete /></el-icon></el-button>
                    </div>
                </div>
                <div class="fd-node-body">
                    <template v-if="node.component === 'container'">
                        <div
                            class="fd-container"
                            :class="{ 'fd-drop-active': isContainerDropActive(node.id) }"
                            :style="containerStyle(node)"
                            @dragenter.stop.prevent="onContainerDragOver(node.id)"
                            @dragover.stop.prevent="onContainerDragOver(node.id)"
                            @dragleave.stop="onContainerDragLeave($event, node.id)"
                            @drop.stop="onContainerDrop(node.id)">
                            <div v-if="!(node.children || []).length" class="fd-container-empty">
                                拖字段到容器内
                            </div>
                            <designer-node-item
                                v-for="child in (node.children || [])"
                                :key="child.id"
                                :node="child"
                                :selected-node-id="selectedNodeId"
                                :component-label="componentLabel"
                                :select-node="selectNode"
                                :move-node="moveNode"
                                :copy-node="copyNode"
                                :remove-node="removeNode"
                                :on-node-drag-start="onNodeDragStart"
                                :on-node-drop="onNodeDrop"
                                :on-container-drop="onContainerDrop"
                                :on-container-drag-over="onContainerDragOver"
                                :on-container-drag-leave="onContainerDragLeave"
                                :is-container-drop-active="isContainerDropActive"
                                :on-node-drag-enter="onNodeDragEnter"
                                :is-node-drop-target="isNodeDropTarget"
                                :container-style="containerStyle"
                                :child-mode="true"></designer-node-item>
                        </div>
                    </template>
                    <template v-else>
                        <component-preview :node="node" :component-label="componentLabel"></component-preview>
                    </template>
                </div>
            </div>
        `,
    };

    const PreviewFieldRender = {
        name: "PreviewFieldRender",
        props: {
            node: {
                type: Object,
                required: true,
            },
            formData: {
                type: Object,
                required: true,
            },
            componentLabel: {
                type: Function,
                required: true,
            },
            containerStyle: {
                type: Function,
                required: true,
            },
            runScript: {
                type: Function,
                required: true,
            },
        },
        emits: ["file-change"],
        methods: {
            onFieldChange(value) {
                if (!this.node || !this.node.key) return;
                this.formData[this.node.key] = value;
                this.runScript(this.node, value, this.formData);
            },
            resolveVariableValue(node) {
                const fallbackKey = VARIABLE_META_MAP[node?.component]?.key || "";
                const variableKey = String(node?.variable_key || fallbackKey).trim();
                return resolveVariableValueByKey(variableKey);
            },
            withAlignStyle(node) {
                return buildTextDisplayStyle(node);
            },
            onFileChange(evt) {
                this.$emit("file-change", {
                    field: this.node,
                    files: Array.from(evt?.target?.files || []),
                });
            },
        },
        template: `
            <div class="fd-preview-node">
                <h1
                    v-if="node.component === 'title_h1'"
                    class="fd-preview-heading fd-preview-h1"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '一级标题' ]]</h1>

                <h2
                    v-else-if="node.component === 'title_h2'"
                    class="fd-preview-heading fd-preview-h2"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '二级标题' ]]</h2>

                <h3
                    v-else-if="node.component === 'title_h3'"
                    class="fd-preview-heading fd-preview-h3"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '三级标题' ]]</h3>

                <h4
                    v-else-if="node.component === 'title_h4'"
                    class="fd-preview-heading fd-preview-h4"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '四级标题' ]]</h4>

                <h5
                    v-else-if="node.component === 'title_h5'"
                    class="fd-preview-heading fd-preview-h5"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '五级标题' ]]</h5>

                <p
                    v-else-if="node.component === 'paragraph'"
                    class="fd-preview-paragraph"
                    :style="withAlignStyle(node)">[[ node.content || node.label || '文本内容' ]]</p>

                <div
                    v-else-if="node.component === 'var_username' || node.component === 'var_phone' || node.component === 'var_full_name'"
                    class="fd-preview-variable"
                    :style="node.css_text || ''">
                    [[ node.variable_label || node.label || '变量' ]]: [[ resolveVariableValue(node) || '-' ]]
                </div>

                <div
                    v-else-if="node.component === 'placeholder'"
                    class="fd-preview-placeholder"
                    :style="node.css_text || ''">
                    [[ node.content || '' ]]
                </div>

                <div v-else-if="node.component === 'container'" class="workflow-form-container-block" style="margin-bottom: 12px;">
                    <div class="workflow-form-container-canvas" :style="containerStyle(node)">
                        <div v-if="!(node.children || []).length" class="workflow-form-container-empty">拖字段到容器内</div>
                        <div v-for="child in (node.children || [])" :key="child.id || child.key || child.label" class="workflow-form-container-item">
                            <preview-field-render
                                :node="child"
                                :form-data="formData"
                                :component-label="componentLabel"
                                :container-style="containerStyle"
                                :run-script="runScript"
                                @file-change="$emit('file-change', $event)"></preview-field-render>
                        </div>
                    </div>
                </div>

                    <el-form-item v-else :label="node.label || node.key" :prop="node.key || undefined" :required="node.required">
                        <el-input
                            v-if="node.component === 'input'"
                            v-model="formData[node.key]"
                            :placeholder="node.placeholder || '请输入'"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])"
                        clearable></el-input>

                    <el-input
                        v-else-if="node.component === 'textarea'"
                        v-model="formData[node.key]"
                        type="textarea"
                        :rows="node.rows || 3"
                        :placeholder="node.placeholder || '请输入'"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])"></el-input>

                    <el-input-number
                        v-else-if="node.component === 'number'"
                        v-model="formData[node.key]"
                        :min="node.min"
                        :max="node.max"
                        :step="node.step || 1"
                        style="width: 100%;"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])"></el-input-number>

                    <input
                        v-else-if="node.component === 'file'"
                        type="file"
                        class="workflow-native-file"
                        :accept="node.accept || ''"
                        :multiple="node.multiple"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFileChange" />

                    <signature-field
                        v-else-if="node.component === 'signature'"
                        v-model="formData[node.key]"
                        :placeholder="node.placeholder || '请在此处手写签名'"
                        :disabled="!!node.disabled"
                        :style="node.css_text || ''"
                        @change="onFieldChange($event)"></signature-field>

                    <el-radio-group
                        v-else-if="node.component === 'radio'"
                        v-model="formData[node.key]"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])">
                        <el-radio
                            v-for="(opt, idx) in node.options || []"
                            :key="opt.id || idx"
                            :label="opt.value">[[ opt.label || '选项' ]]</el-radio>
                    </el-radio-group>

                    <el-checkbox-group
                        v-else-if="node.component === 'checkbox'"
                        v-model="formData[node.key]"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])">
                        <el-checkbox
                            v-for="(opt, idx) in node.options || []"
                            :key="opt.id || idx"
                            :label="opt.value">[[ opt.label || '选项' ]]</el-checkbox>
                    </el-checkbox-group>

                    <el-select
                        v-else-if="node.component === 'select'"
                        v-model="formData[node.key]"
                        :placeholder="node.placeholder || '请选择'"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])">
                        <el-option
                            v-for="(opt, idx) in node.options || []"
                            :key="opt.id || idx"
                            :label="opt.label || '选项'"
                            :value="opt.value"></el-option>
                    </el-select>

                    <el-switch
                        v-else-if="node.component === 'switch'"
                        v-model="formData[node.key]"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])"></el-switch>

                    <el-date-picker
                        v-else-if="node.component === 'date'"
                        v-model="formData[node.key]"
                        type="date"
                        value-format="YYYY-MM-DD"
                        :placeholder="node.placeholder || '请选择日期'"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])"></el-date-picker>

                    <el-date-picker
                        v-else-if="node.component === 'datetime'"
                        v-model="formData[node.key]"
                        type="datetime"
                        value-format="YYYY-MM-DD HH:mm:ss"
                        :placeholder="node.placeholder || '请选择日期时间'"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])"></el-date-picker>

                    <el-input
                        v-else
                        v-model="formData[node.key]"
                        :placeholder="node.placeholder || '请输入'"
                        :style="node.css_text || ''"
                        :disabled="!!node.disabled"
                        @change="onFieldChange(formData[node.key])"
                        clearable></el-input>
                </el-form-item>
            </div>
        `,
    };
    PreviewFieldRender.components = {
        PreviewFieldRender,
        SignatureField,
    };

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

            const componentGroups = [
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
                        { value: "placeholder", label: "占位符", thumb: "___" },
                    ],
                },
                {
                    key: "text",
                    title: "文本组件",
                    list: [
                        { value: "title_h1", label: "一级标题", thumb: "H1" },
                        { value: "title_h2", label: "二级标题", thumb: "H2" },
                        { value: "title_h3", label: "三级标题", thumb: "H3" },
                        { value: "title_h4", label: "四级标题", thumb: "H4" },
                        { value: "title_h5", label: "五级标题", thumb: "H5" },
                        { value: "paragraph", label: "文本", thumb: "TXT" },
                    ],
                },
            ];

            const componentPalette = componentGroups.flatMap((group) => group.list);
            const componentValueSet = new Set(componentPalette.map((item) => item.value));
            const componentLabelMap = componentPalette.reduce((acc, item) => {
                acc[item.value] = item.label;
                return acc;
            }, {});

            const componentAliasMap = {
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
            };

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

    const getDefaultFieldDataSources = (node) => getAvailableFieldDataSources(
        fieldDataSourceMetadata,
        "default",
        node?.component,
    );

    const getOptionsFieldDataSources = (node) => getAvailableFieldDataSources(
        fieldDataSourceMetadata,
        "options",
        node?.component,
    );

    const hasCompatibleFieldDataSources = (node, target) => {
        const list = target === "default"
            ? getDefaultFieldDataSources(node)
            : getOptionsFieldDataSources(node);
        return list.length > 0;
    };

    const isDualSupportDataSource = (sourceKey, component) => {
        if (!sourceKey) return false;
        const source = getFieldDataSourceByKey(fieldDataSourceMetadata, sourceKey);
        const defaultMethod = getFieldSourceMethodName?.("default", component);
        const optionsMethod = getFieldSourceMethodName?.("options", component);
        const supportedMethods = Array.isArray(source?.supported_methods) ? source.supported_methods : [];
        return !!source && !!defaultMethod && !!optionsMethod
            && supportedMethods.includes(defaultMethod)
            && supportedMethods.includes(optionsMethod);
    };

    const refreshFieldDataSourceMetadata = (items) => {
        fieldDataSourceMetadata = normalizeFieldDataSourceMetadata(items || []);
    };

    const fetchFieldDataSourceMetadata = async () => {
        if (fieldDataSourceMetadata?.length) return;
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
                return getFieldSourceParamSchema(fieldDataSourceMetadata, ui?.source_key, target);
            };

            const onFieldDataSourceChange = (node, target) => {
                const ui = target === "default" ? node?.default_source_ui : node?.options_source_ui;
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
                nodeId: "",
                nodeRef: null,
                title: "选择数据源类",
                selectedKey: "",
                page: 1,
                pageSize: 8,
                options: [],
            });

            const getFieldDataSourcePickerNode = () => {
                if (fieldDataSourcePicker.nodeRef && typeof fieldDataSourcePicker.nodeRef === "object") {
                    return fieldDataSourcePicker.nodeRef;
                }
                const form = activeForm.value;
                if (!form || !fieldDataSourcePicker.nodeId) return null;
                return findNodeLocation(form, fieldDataSourcePicker.nodeId)?.node || null;
            };

            const getFieldDataSourceKeyLabel = (key, target, node) => {
                const cleanKey = String(key || "").trim().toLowerCase();
                if (!cleanKey) return "";
                const list = target === "default"
                    ? getDefaultFieldDataSources(node)
                    : getOptionsFieldDataSources(node);
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
                fieldDataSourcePicker.options = target === "default"
                    ? getDefaultFieldDataSources(node)
                    : getOptionsFieldDataSources(node);
                fieldDataSourcePicker.selectedKey = String(
                    (target === "default" ? node?.default_source_ui?.source_key : node?.options_source_ui?.source_key) || ""
                ).trim().toLowerCase();
                fieldDataSourcePicker.page = 1;
                fieldDataSourcePicker.title = target === "default"
                    ? "选择默认值数据源类"
                    : "选择选项数据源类";
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
                const ui = target === "default"
                    ? node.default_source_ui
                    : node.options_source_ui;
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
