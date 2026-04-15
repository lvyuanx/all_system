export const buildTextDisplayStyle = (node) => {
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

export const buildDividerStyle = (node) => {
    const lineStyle = String(node?.line_style || "solid").trim() || "solid";
    const lineColor = String(node?.line_color || "#d7deea").trim() || "#d7deea";
    const thicknessRaw = Number(node?.line_thickness);
    const marginRaw = Number(node?.line_margin);
    const thickness = Number.isFinite(thicknessRaw) ? Math.max(1, thicknessRaw) : 1;
    const margin = Number.isFinite(marginRaw) ? Math.max(0, marginRaw) : 12;
    const base = [
        "border:0",
        `border-top:${thickness}px ${lineStyle} ${lineColor}`,
        `margin:${margin}px 0`,
        "width:100%",
    ].join(";");
    const custom = String(node?.css_text || "").trim();
    return custom ? `${base};${custom}` : base;
};

export const buildSpacerStyle = (node) => {
    const heightRaw = Number(node?.height);
    const height = Number.isFinite(heightRaw) ? Math.max(0, heightRaw) : 24;
    const base = [
        "display:block",
        "width:100%",
        `height:${height}px`,
        "min-height:1px",
    ].join(";");
    const custom = String(node?.css_text || "").trim();
    return custom ? `${base};${custom}` : base;
};

export const buildCardBlockStyle = (node) => {
    const paddingRaw = Number(node?.card_padding);
    const radiusRaw = Number(node?.card_radius);
    const padding = Number.isFinite(paddingRaw) ? Math.max(0, paddingRaw) : 12;
    const radius = Number.isFinite(radiusRaw) ? Math.max(0, radiusRaw) : 10;
    const shadow = !!node?.card_shadow
        ? "0 8px 24px rgba(15, 23, 42, 0.08)"
        : "0 1px 2px rgba(15, 23, 42, 0.06)";
    const base = [
        `padding:${padding}px`,
        `border-radius:${radius}px`,
        "border:1px solid #d7deea",
        "background:#fff",
        `box-shadow:${shadow}`,
    ].join(";");
    const custom = String(node?.css_text || "").trim();
    return custom ? `${base};${custom}` : base;
};

export const resolveSourceAwareDisplayContent = (node, fallback = "") => {
    const fixed = String(node?.content || fallback || "");
    const mode = String(node?.default_source_ui?.mode || "fixed").trim();
    if (mode === "fixed") return fixed;
    const fallbackValue = String(node?.default_source_ui?.fallback_value || "").trim();
    if (fallbackValue) return fallbackValue;
    return fixed;
};

export const toInlineStyle = (styleObject = {}) =>
    Object.entries(styleObject)
        .filter(([, value]) => value !== undefined && value !== null && value !== "")
        .map(([key, value]) => `${key}:${value}`)
        .join(";");

export const containerStyle = (node) => {
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
