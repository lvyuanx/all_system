import { VARIABLE_META_MAP } from "./form_designer_constants.js";
import {
    buildCardBlockStyle,
    buildDividerStyle,
    buildSpacerStyle,
    buildTextDisplayStyle,
    resolveSourceAwareDisplayContent,
} from "./form_designer_style.js";

export function createComponentPreview(resolveVariableValueByKey = () => "") {
    return {
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
        },
        template: `
            <div>
                <h1 v-if="node.component === 'title_h1'" class="fd-preview-heading fd-preview-h1" :style="withAlignStyle(node)">[[ node.content || node.label || '一级标题' ]]</h1>
                <h2 v-else-if="node.component === 'title_h2'" class="fd-preview-heading fd-preview-h2" :style="withAlignStyle(node)">[[ node.content || node.label || '二级标题' ]]</h2>
                <h3 v-else-if="node.component === 'title_h3'" class="fd-preview-heading fd-preview-h3" :style="withAlignStyle(node)">[[ node.content || node.label || '三级标题' ]]</h3>
                <h4 v-else-if="node.component === 'title_h4'" class="fd-preview-heading fd-preview-h4" :style="withAlignStyle(node)">[[ node.content || node.label || '四级标题' ]]</h4>
                <h5 v-else-if="node.component === 'title_h5'" class="fd-preview-heading fd-preview-h5" :style="withAlignStyle(node)">[[ node.content || node.label || '五级标题' ]]</h5>
                <p v-else-if="node.component === 'paragraph'" class="fd-preview-paragraph" :style="withAlignStyle(node)">[[ node.content || node.label || '文本内容' ]]</p>
                <div v-else-if="node.component === 'var_username' || node.component === 'var_phone' || node.component === 'var_full_name'" class="fd-preview-variable" :style="node.css_text || ''">
                    [[ node.variable_label || node.label || componentLabel(node.component) ]]: [[ resolveVariableValue(node) || '-' ]]
                </div>
                <div v-else-if="node.component === 'placeholder'" class="fd-preview-placeholder" :style="node.css_text || ''">[[ node.content || '占位符' ]]</div>
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
                <el-input v-else-if="node.component === 'input'" class="fd-preview-control" :placeholder="node.placeholder || '请输入'" disabled :style="node.css_text || ''"></el-input>
                <el-input v-else-if="node.component === 'textarea'" type="textarea" :rows="node.rows || 3" class="fd-preview-control" :placeholder="node.placeholder || '请输入'" disabled :style="node.css_text || ''"></el-input>
                <el-input-number v-else-if="node.component === 'number'" class="fd-preview-control" :min="node.min" :max="node.max" :step="node.step || 1" disabled style="width: 100%;" :style="node.css_text || ''"></el-input-number>
                <div v-else-if="node.component === 'file'" class="fd-preview-text" :style="node.css_text || ''">文件上传控件</div>
                <div v-else-if="node.component === 'signature'" class="fd-preview-text" :style="node.css_text || ''">手写签名控件</div>
                <el-radio-group v-else-if="node.component === 'radio'" class="fd-preview-control" disabled :style="node.css_text || ''">
                    <el-radio v-for="(opt, idx) in node.options || []" :key="opt.id || idx" :label="opt.value">[[ opt.label || '选项' ]]</el-radio>
                </el-radio-group>
                <el-checkbox-group v-else-if="node.component === 'checkbox'" class="fd-preview-control" disabled :style="node.css_text || ''">
                    <el-checkbox v-for="(opt, idx) in node.options || []" :key="opt.id || idx" :label="opt.value">[[ opt.label || '选项' ]]</el-checkbox>
                </el-checkbox-group>
                <el-select v-else-if="node.component === 'select'" class="fd-preview-control" :placeholder="node.placeholder || '请选择'" disabled :style="node.css_text || ''">
                    <el-option v-for="(opt, idx) in node.options || []" :key="opt.id || idx" :label="opt.label || '选项'" :value="opt.value"></el-option>
                </el-select>
                <el-switch v-else-if="node.component === 'switch'" disabled :style="node.css_text || ''"></el-switch>
                <el-date-picker v-else-if="node.component === 'date'" class="fd-preview-control" type="date" placeholder="请选择日期" disabled :style="node.css_text || ''"></el-date-picker>
                <el-date-picker v-else-if="node.component === 'datetime'" class="fd-preview-control" type="datetime" placeholder="请选择日期时间" disabled :style="node.css_text || ''"></el-date-picker>
                <div v-else class="fd-preview-text">[[ componentLabel(node.component) ]] 预览</div>
            </div>
        `,
    };
}
