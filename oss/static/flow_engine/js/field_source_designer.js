const cloneValue = (value) => {
    if (value === undefined) return undefined;
    return JSON.parse(JSON.stringify(value));
};

const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj || {}, key);
const COMPONENT_VALUE_TYPES = {
    input: "text",
    textarea: "text",
    number: "number",
    title_h1: "text",
    title_h2: "text",
    title_h3: "text",
    title_h4: "text",
    title_h5: "text",
    paragraph: "text",
    select: "options",
    radio: "options",
    checkbox: "options",
    switch: "boolean",
    date: "date",
    datetime: "datetime",
    file: "file",
};
const CONTEXT_WRITE_TARGETS = ["none", "flow", "node", "both"];

const inferWriteTarget = (raw) => {
    const explicitTarget = String(raw?.write_target || "").trim().toLowerCase();
    if (CONTEXT_WRITE_TARGETS.includes(explicitTarget)) return explicitTarget;
    const legacyPath = String(raw?.write_path || "").trim();
    if (!legacyPath) return "node";
    if (legacyPath.startsWith("form.")) return "node";
    if (!legacyPath.includes(".")) return "flow";
    return "node";
};

export const getFieldSourceMethodName = (target, component) => {
    const cleanTarget = String(target || "").trim().toLowerCase();
    const cleanComponent = String(component || "").trim().toLowerCase();
    const valueType = COMPONENT_VALUE_TYPES[cleanComponent];
    if (!["default", "options"].includes(cleanTarget) || !valueType) return "";
    return `get_${cleanTarget}_${valueType}`;
};

const supportsComponentFamily = (supportedComponents, component) => {
    const cleanComponent = String(component || "").trim().toLowerCase();
    if (!cleanComponent) return true;
    const expectedType = COMPONENT_VALUE_TYPES[cleanComponent];
    return (supportedComponents || []).some((item) => {
        const cleanItem = String(item || "").trim().toLowerCase();
        if (!cleanItem) return false;
        return cleanItem === cleanComponent || (
            !!expectedType && COMPONENT_VALUE_TYPES[cleanItem] === expectedType
        );
    });
};

const buildLegacySupportedMethods = (item) => {
    const components = Array.isArray(item.support_components) ? item.support_components : [];
    const methods = new Set();
    if (item.support_default) {
        components.forEach((component) => {
            const methodName = getFieldSourceMethodName("default", component);
            if (methodName) methods.add(methodName);
        });
    }
    if (item.support_options) {
        components.forEach((component) => {
            const methodName = getFieldSourceMethodName("options", component);
            if (methodName) methods.add(methodName);
        });
    }
    return Array.from(methods);
};

const normalizeMetadataInput = (items) => {
    if (Array.isArray(items)) return items;
    if (items && typeof items === "object") {
        if (Array.isArray(items.items)) return items.items;
        if (Array.isArray(items.data)) return items.data;
    }
    return [];
};

export const normalizeFieldDataSourceMetadata = (items) => {
    const list = normalizeMetadataInput(items);
    if (!list.length) return [];
    return list
        .map((item) => {
            if (!item || typeof item !== "object") return null;
            const key = String(item.key || "").trim().toLowerCase();
            if (!key) return null;
            return {
                key,
                label: String(item.label || key).trim(),
                data_type: String(item.data_type || "").trim().toLowerCase(),
                support_components: Array.isArray(item.support_components)
                    ? item.support_components
                        .map((component) => String(component || "").trim().toLowerCase())
                        .filter(Boolean)
                    : [],
                supported_methods: (
                    Array.isArray(item.supported_methods)
                        ? item.supported_methods
                        : buildLegacySupportedMethods(item)
                )
                    .map((methodName) => String(methodName || "").trim().toLowerCase())
                    .filter(Boolean),
            };
        })
        .filter(Boolean);
};

const normalizeLegacyDefaultConfig = (rawConfig, defaultValue) => {
    const raw = rawConfig && typeof rawConfig === "object" ? rawConfig : {};
    return {
        source_type: String(raw.source_type || "literal").trim().toLowerCase(),
        value: own(raw, "value") ? cloneValue(raw.value) : cloneValue(defaultValue),
        context_path: String(raw.context_path || "").trim(),
        enum_code: String(raw.enum_code || "").trim(),
        db_source_code: String(raw.db_source_code || "").trim(),
        fallback_value: own(raw, "fallback_value") ? cloneValue(raw.fallback_value) : "",
    };
};

const normalizeLegacyOptionsConfig = (rawConfig) => {
    const raw = rawConfig && typeof rawConfig === "object" ? rawConfig : {};
    return {
        source_type: String(raw.source_type || "manual").trim().toLowerCase(),
        context_path: String(raw.context_path || "").trim(),
        enum_code: String(raw.enum_code || "").trim(),
        db_source_code: String(raw.db_source_code || "").trim(),
        label_key: String(raw.label_key || "label").trim(),
        value_key: String(raw.value_key || "value").trim(),
        fallback_to_manual: own(raw, "fallback_to_manual") ? !!raw.fallback_to_manual : true,
    };
};

const hasLegacyDefaultConfig = (config) => {
    if (!config || typeof config !== "object") return false;
    const normalized = normalizeLegacyDefaultConfig(config);
    return normalized.source_type !== "literal"
        || normalized.context_path
        || normalized.enum_code
        || normalized.db_source_code
        || (normalized.fallback_value !== "" && normalized.fallback_value !== undefined && normalized.fallback_value !== null);
};

const hasLegacyOptionsConfig = (config) => {
    if (!config || typeof config !== "object") return false;
    const normalized = normalizeLegacyOptionsConfig(config);
    return normalized.source_type !== "manual"
        || normalized.context_path
        || normalized.enum_code
        || normalized.db_source_code
        || normalized.label_key !== "label"
        || normalized.value_key !== "value"
        || !normalized.fallback_to_manual;
};

const normalizeMode = (rawConfig) => {
    const config = rawConfig && typeof rawConfig === "object" ? rawConfig : {};
    const rawMode = String(config.mode || "").trim().toLowerCase();
    if (rawMode) return rawMode;
    if (config.source_key) return "data_source";
    if (own(config, "value")) return "fixed";
    return "";
};

export const normalizeDefaultSourceUi = (field, defaultValue) => {
    const sourceConfig = field?.default_source_config && typeof field.default_source_config === "object"
        ? field.default_source_config
        : {};
    const sourceMode = normalizeMode(sourceConfig);
    const legacyConfig = normalizeLegacyDefaultConfig(field?.default_config, defaultValue);
    const ui = {
        mode: "fixed",
        source_key: "",
        source_params: {},
        fallback_value: "",
        legacy_config: hasLegacyDefaultConfig(field?.default_config) ? legacyConfig : null,
    };
    if (sourceMode === "data_source") {
        ui.mode = "data_source";
        ui.source_key = String(sourceConfig.source_key || "").trim().toLowerCase();
        ui.source_params = sourceConfig.source_params && typeof sourceConfig.source_params === "object"
            ? cloneValue(sourceConfig.source_params)
            : {};
        ui.fallback_value = own(sourceConfig, "fallback_value") ? cloneValue(sourceConfig.fallback_value) : "";
        return ui;
    }
    if (sourceMode && sourceMode !== "fixed" && sourceMode !== "literal" && sourceMode !== "manual") {
        ui.mode = "fixed";
        return ui;
    }
    if (hasLegacyDefaultConfig(field?.default_config)) return ui;
    if (own(sourceConfig, "fallback_value")) {
        ui.fallback_value = cloneValue(sourceConfig.fallback_value);
    }
    return ui;
};

export const normalizeOptionsSourceUi = (field) => {
    const sourceConfig = field?.options_source_config && typeof field.options_source_config === "object"
        ? field.options_source_config
        : {};
    const sourceMode = normalizeMode(sourceConfig);
    const legacyConfig = normalizeLegacyOptionsConfig(field?.options_config);
    const ui = {
        mode: "manual",
        source_key: "",
        source_params: {},
        fallback_to_manual: own(sourceConfig, "fallback_to_manual") ? !!sourceConfig.fallback_to_manual : true,
        legacy_config: hasLegacyOptionsConfig(field?.options_config) ? legacyConfig : null,
    };
    if (sourceMode === "data_source") {
        ui.mode = "data_source";
        ui.source_key = String(sourceConfig.source_key || "").trim().toLowerCase();
        ui.source_params = sourceConfig.source_params && typeof sourceConfig.source_params === "object"
            ? cloneValue(sourceConfig.source_params)
            : {};
        return ui;
    }
    if (hasLegacyOptionsConfig(field?.options_config)) return ui;
    return ui;
};

export const shouldShowLegacyDefaultMode = () => false;

export const shouldShowLegacyOptionsMode = () => false;

export const getAvailableFieldDataSources = (items, target, component) => {
    const cleanTarget = String(target || "").trim().toLowerCase();
    const cleanComponent = String(component || "").trim().toLowerCase();
    const methodName = getFieldSourceMethodName(cleanTarget, cleanComponent);
    return normalizeFieldDataSourceMetadata(items).filter((item) => {
        const supportedMethods = Array.isArray(item.supported_methods) ? item.supported_methods : [];
        const supportsTarget = supportedMethods.some((name) => name.startsWith(`get_${cleanTarget}_`));
        if (!supportsTarget) return false;
        if (!item.support_components.length) {
            if (!cleanComponent) return true;
            return !!methodName && supportedMethods.includes(methodName);
        }
        if (cleanComponent && !supportsComponentFamily(item.support_components, cleanComponent)) return false;
        if (!cleanComponent) return true;
        return !!methodName && supportedMethods.includes(methodName);
    });
};

export const getFieldDataSourceByKey = (items, key) => {
    const cleanKey = String(key || "").trim().toLowerCase();
    if (!cleanKey) return null;
    return normalizeFieldDataSourceMetadata(items).find((item) => item.key === cleanKey) || null;
};

export const getFieldSourceParamSchema = (items, key, target) => {
    return [];
};

export const syncFieldSourceParamsBySchema = (items, key, target, sourceParams) => {
    const schema = getFieldSourceParamSchema(items, key, target);
    const current = sourceParams && typeof sourceParams === "object" ? sourceParams : {};
    if (!schema.length) return cloneValue(current) || {};
    const normalized = {};
    schema.forEach((item) => {
        if (!item?.name) return;
        if (own(current, item.name)) {
            normalized[item.name] = cloneValue(current[item.name]);
            return;
        }
    });
    return normalized;
};

export const buildDefaultSourcePayload = (field) => {
    const ui = field?.default_source_ui;
    const payload = {};
    const hasNewDataSource = ui?.mode === "data_source" && ui.source_key;
    if (hasNewDataSource) {
        payload.default_source_config = {
            mode: "data_source",
            source_key: String(ui.source_key).trim().toLowerCase(),
            source_params: cloneValue(ui.source_params || {}),
        };
        if (ui.fallback_value !== "" && ui.fallback_value !== undefined && ui.fallback_value !== null) {
            payload.default_source_config.fallback_value = cloneValue(ui.fallback_value);
        }
    }
    const legacy = ui?.legacy_config;
    if (legacy && !hasNewDataSource) {
        const normalized = normalizeLegacyDefaultConfig(legacy, field?.default);
        if (hasLegacyDefaultConfig(normalized)) {
            payload.default_config = normalized;
        }
    }
    return payload;
};

export const buildOptionsSourcePayload = (field) => {
    const ui = field?.options_source_ui;
    const payload = {};
    const hasNewDataSource = ui?.mode === "data_source" && ui.source_key;
    if (hasNewDataSource) {
        payload.options_source_config = {
            mode: "data_source",
            source_key: String(ui.source_key).trim().toLowerCase(),
            source_params: cloneValue(ui.source_params || {}),
            fallback_to_manual: !!ui.fallback_to_manual,
        };
    }
    const legacy = ui?.legacy_config;
    if (legacy && !hasNewDataSource) {
        const normalized = normalizeLegacyOptionsConfig(legacy);
        if (hasLegacyOptionsConfig(normalized)) {
            payload.options_config = normalized;
        }
    }
    return payload;
};

export const normalizeContextBindingUi = (field) => {
    const raw = field?.context_binding;
    const extras = {};
    if (raw && typeof raw === "object") {
        Object.keys(raw).forEach((key) => {
            if (!["read_path", "write_path", "write_mode", "write_target"].includes(key)) {
                extras[key] = cloneValue(raw[key]);
            }
        });
    }
    return {
        write_target: inferWriteTarget(raw),
        write_mode: ["overwrite", "merge_if_absent"].includes(raw?.write_mode)
            ? raw.write_mode
            : "overwrite",
        legacy_config: Object.keys(extras).length ? extras : null,
    };
};

export const buildContextBindingPayload = (field) => {
    const binding = field?.context_binding;
    if (!binding || typeof binding !== "object") return {};
    const payload = binding.legacy_config && typeof binding.legacy_config === "object"
        ? cloneValue(binding.legacy_config)
        : {};
    const writeTarget = CONTEXT_WRITE_TARGETS.includes(binding.write_target)
        ? binding.write_target
        : "node";
    const writeMode = ["overwrite", "merge_if_absent"].includes(binding.write_mode)
        ? binding.write_mode
        : "overwrite";
    if (writeTarget !== "node") payload.write_target = writeTarget;
    if (writeTarget !== "none" && writeMode !== "overwrite") payload.write_mode = writeMode;
    return Object.keys(payload).length ? { context_binding: payload } : {};
};

export const shouldUseManualOptions = (field) => {
    const ui = field?.options_source_ui;
    if (ui?.mode === "manual") return true;
    if (ui?.mode === "data_source") return !!ui.fallback_to_manual;
    if (ui?.mode === "legacy") {
        const legacy = ui.legacy_config || {};
        const sourceType = String(legacy.source_type || "manual").trim().toLowerCase();
        return sourceType === "manual" || !!legacy.fallback_to_manual;
    }
    return true;
};
