const cloneValue = (value) => {
    if (value === undefined) return undefined;
    return JSON.parse(JSON.stringify(value));
};

const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj || {}, key);

const normalizeSchemaItem = (item) => {
    if (!item || typeof item !== "object") return null;
    return {
        name: String(item.name || "").trim(),
        label: String(item.label || item.name || "").trim(),
        target: String(item.target || "").trim().toLowerCase(),
        component: String(item.component || "input").trim().toLowerCase(),
        placeholder: String(item.placeholder || "").trim(),
        help: String(item.help || item.description || "").trim(),
        options: Array.isArray(item.options)
            ? item.options
                .map((option) => {
                    if (option && typeof option === "object") {
                        return {
                            label: String(option.label ?? option.name ?? option.value ?? "").trim(),
                            value: option.value ?? option.key ?? option.label ?? option.name ?? "",
                        };
                    }
                    return {
                        label: String(option ?? "").trim(),
                        value: option ?? "",
                    };
                })
                .filter((option) => option.label || option.value !== "")
            : [],
    };
};

export const normalizeFieldDataSourceMetadata = (items) => {
    if (!Array.isArray(items)) return [];
    return items
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
                support_default: !!item.support_default,
                support_options: !!item.support_options,
                params_schema: Array.isArray(item.params_schema)
                    ? item.params_schema.map(normalizeSchemaItem).filter(Boolean)
                    : [],
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
    if (hasLegacyDefaultConfig(field?.default_config)) {
        ui.mode = "legacy";
        return ui;
    }
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
    if (hasLegacyOptionsConfig(field?.options_config)) {
        ui.mode = "legacy";
        return ui;
    }
    return ui;
};

export const shouldShowLegacyDefaultMode = (field) =>
    field?.default_source_ui?.mode === "legacy" || !!field?.default_source_ui?.legacy_config;

export const shouldShowLegacyOptionsMode = (field) =>
    field?.options_source_ui?.mode === "legacy" || !!field?.options_source_ui?.legacy_config;

export const getAvailableFieldDataSources = (items, target, component) => {
    const cleanTarget = String(target || "").trim().toLowerCase();
    const cleanComponent = String(component || "").trim().toLowerCase();
    return normalizeFieldDataSourceMetadata(items).filter((item) => {
        if (cleanTarget === "default" && !item.support_default) return false;
        if (cleanTarget === "options" && !item.support_options) return false;
        if (!item.support_components.length) return true;
        return item.support_components.includes(cleanComponent);
    });
};

export const getFieldDataSourceByKey = (items, key) => {
    const cleanKey = String(key || "").trim().toLowerCase();
    if (!cleanKey) return null;
    return normalizeFieldDataSourceMetadata(items).find((item) => item.key === cleanKey) || null;
};

export const getFieldSourceParamSchema = (items, key, target) => {
    const source = getFieldDataSourceByKey(items, key);
    if (!source) return [];
    const cleanTarget = String(target || "").trim().toLowerCase();
    return (source.params_schema || []).filter((item) => !item.target || item.target === cleanTarget);
};

export const syncFieldSourceParamsBySchema = (items, key, target, sourceParams) => {
    const schema = getFieldSourceParamSchema(items, key, target);
    if (!schema.length) return {};
    const current = sourceParams && typeof sourceParams === "object" ? sourceParams : {};
    const normalized = {};
    schema.forEach((item) => {
        if (!item?.name) return;
        if (own(current, item.name)) {
            normalized[item.name] = cloneValue(current[item.name]);
            return;
        }
        normalized[item.name] = item.component === "switch" ? false : "";
    });
    return normalized;
};

export const buildDefaultSourcePayload = (field) => {
    const ui = field?.default_source_ui;
    const payload = {};
    if (ui?.mode === "data_source" && ui.source_key) {
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
    if (legacy && (ui.mode === "legacy" || ui.mode === "data_source")) {
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
    if (ui?.mode === "data_source" && ui.source_key) {
        payload.options_source_config = {
            mode: "data_source",
            source_key: String(ui.source_key).trim().toLowerCase(),
            source_params: cloneValue(ui.source_params || {}),
            fallback_to_manual: !!ui.fallback_to_manual,
        };
    }
    const legacy = ui?.legacy_config;
    if (legacy && (ui.mode === "legacy" || ui.mode === "data_source")) {
        const normalized = normalizeLegacyOptionsConfig(legacy);
        if (hasLegacyOptionsConfig(normalized)) {
            payload.options_config = normalized;
        }
    }
    return payload;
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
