import { createSignatureFieldComponent } from "./signature_field.js";
import { VARIABLE_META_MAP } from "./form_designer_constants.js";
import {
    buildCardBlockStyle,
    buildDividerStyle,
    buildSpacerStyle,
    buildTextDisplayStyle,
    resolveSourceAwareDisplayContent,
} from "./form_designer_style.js";

export function createPreviewFieldRender(resolveVariableValueByKey = () => "") {
    const SignatureField = createSignatureFieldComponent();
    const PreviewFieldRender = {
        name: "PreviewFieldRender",
        props: {
            node: { type: Object, required: true },
            formData: { type: Object, required: true },
            componentLabel: { type: Function, required: true },
            containerStyle: { type: Function, required: true },
            runScript: { type: Function, required: true },
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
            withDividerStyle(node) {
                return buildDividerStyle(node);
            },
            withSpacerStyle(node) {
                return buildSpacerStyle(node);
            },
            withCardStyle(node) {
                return buildCardBlockStyle(node);
            },
            resolveDisplayContent(node, fallback) {
                return resolveSourceAwareDisplayContent(node, fallback);
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
                <h1 v-if="node.component === 'title_h1'" class="fd-preview-heading fd-preview-h1" :style="withAlignStyle(node)">[[ node.content || node.label || '一级标题' ]]</h1>
                <h2 v-else-if="node.component === 'title_h2'" class="fd-preview-heading fd-preview-h2" :style="withAlignStyle(node)">[[ node.content || node.label || '二级标题' ]]</h2>
                <h3 v-else-if="node.component === 'title_h3'" class="fd-preview-heading fd-preview-h3" :style="withAlignStyle(node)">[[ node.content || node.label || '三级标题' ]]</h3>
                <h4 v-else-if="node.component === 'title_h4'" class="fd-preview-heading fd-preview-h4" :style="withAlignStyle(node)">[[ node.content || node.label || '四级标题' ]]</h4>
                <h5 v-else-if="node.component === 'title_h5'" class="fd-preview-heading fd-preview-h5" :style="withAlignStyle(node)">[[ node.content || node.label || '五级标题' ]]</h5>
                <p v-else-if="node.component === 'paragraph'" class="fd-preview-paragraph" :style="withAlignStyle(node)">[[ node.content || node.label || '文本内容' ]]</p>
                <div v-else-if="node.component === 'var_username' || node.component === 'var_phone' || node.component === 'var_full_name'" class="fd-preview-variable" :style="node.css_text || ''">
                    [[ node.variable_label || node.label || '变量' ]]: [[ resolveVariableValue(node) || '-' ]]
                </div>
                <div v-else-if="node.component === 'placeholder'" class="fd-preview-placeholder" :style="node.css_text || ''">[[ node.content || '' ]]</div>
                <hr v-else-if="node.component === 'divider'" class="fd-preview-divider" :style="withDividerStyle(node)" />
                <div v-else-if="node.component === 'spacer'" class="fd-preview-spacer" :style="withSpacerStyle(node)"></div>
                <div v-else-if="node.component === 'section_header'" class="fd-preview-section-header" :style="node.css_text || ''">
                    <h4 class="fd-preview-section-title">[[ resolveDisplayContent(node, node.label || '区块标题') || '区块标题' ]]</h4>
                    <p v-if="node.sub_content" class="fd-preview-section-sub">[[ node.sub_content ]]</p>
                </div>
                <div v-else-if="node.component === 'card_block'" class="fd-preview-card-block" :style="withCardStyle(node)">
                    <div class="fd-preview-card-title">[[ node.title || '信息卡片' ]]</div>
                    <p class="fd-preview-card-content">[[ resolveDisplayContent(node, '请填写说明内容') || '请填写说明内容' ]]</p>
                </div>
                <div v-else-if="node.component === 'container'" class="workflow-form-container-block" style="margin-bottom: 12px;">
                    <div class="workflow-form-container-canvas" :style="containerStyle(node)">
                        <div v-if="!(node.children || []).length" class="workflow-form-container-empty">拖字段到容器内</div>
                        <div v-for="child in (node.children || [])" :key="child.id || child.key || child.label" class="workflow-form-container-item">
                            <preview-field-render :node="child" :form-data="formData" :component-label="componentLabel" :container-style="containerStyle" :run-script="runScript" @file-change="$emit('file-change', $event)"></preview-field-render>
                        </div>
                    </div>
                </div>
                <el-form-item v-else :label="node.label || node.key" :prop="node.key || undefined" :required="node.required">
                    <el-input v-if="node.component === 'input'" v-model="formData[node.key]" :placeholder="node.placeholder || '请输入'" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])" clearable></el-input>
                    <el-input v-else-if="node.component === 'textarea'" v-model="formData[node.key]" type="textarea" :rows="node.rows || 3" :placeholder="node.placeholder || '请输入'" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])"></el-input>
                    <el-input-number v-else-if="node.component === 'number'" v-model="formData[node.key]" :min="node.min" :max="node.max" :step="node.step || 1" style="width: 100%;" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])"></el-input-number>
                    <input v-else-if="node.component === 'file'" type="file" class="workflow-native-file" :accept="node.accept || ''" :multiple="node.multiple" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFileChange" />
                    <signature-field v-else-if="node.component === 'signature'" v-model="formData[node.key]" :placeholder="node.placeholder || '请在此处手写签名'" :disabled="!!node.disabled" :style="node.css_text || ''" @change="onFieldChange($event)"></signature-field>
                    <el-radio-group v-else-if="node.component === 'radio'" v-model="formData[node.key]" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])">
                        <el-radio v-for="(opt, idx) in node.options || []" :key="opt.id || idx" :label="opt.value">[[ opt.label || '选项' ]]</el-radio>
                    </el-radio-group>
                    <el-checkbox-group v-else-if="node.component === 'checkbox'" v-model="formData[node.key]" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])">
                        <el-checkbox v-for="(opt, idx) in node.options || []" :key="opt.id || idx" :label="opt.value">[[ opt.label || '选项' ]]</el-checkbox>
                    </el-checkbox-group>
                    <el-select v-else-if="node.component === 'select'" v-model="formData[node.key]" :placeholder="node.placeholder || '请选择'" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])">
                        <el-option v-for="(opt, idx) in node.options || []" :key="opt.id || idx" :label="opt.label || '选项'" :value="opt.value"></el-option>
                    </el-select>
                    <el-switch v-else-if="node.component === 'switch'" v-model="formData[node.key]" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])"></el-switch>
                    <el-date-picker v-else-if="node.component === 'date'" v-model="formData[node.key]" type="date" value-format="YYYY-MM-DD" :placeholder="node.placeholder || '请选择日期'" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])"></el-date-picker>
                    <el-date-picker v-else-if="node.component === 'datetime'" v-model="formData[node.key]" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" :placeholder="node.placeholder || '请选择日期时间'" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])"></el-date-picker>
                    <el-input v-else v-model="formData[node.key]" :placeholder="node.placeholder || '请输入'" :style="node.css_text || ''" :disabled="!!node.disabled" @change="onFieldChange(formData[node.key])" clearable></el-input>
                </el-form-item>
            </div>
        `,
    };
    PreviewFieldRender.components = {
        PreviewFieldRender,
        SignatureField,
    };
    return {
        PreviewFieldRender,
        SignatureField,
    };
}
