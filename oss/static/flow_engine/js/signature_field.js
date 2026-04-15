const DEFAULT_CANVAS_HEIGHT = 160;
const DEFAULT_CANVAS_WIDTH = 320;
const STROKE_COLOR = "#111827";
const STROKE_WIDTH = 2;

const normalizeString = (value) => (typeof value === "string" ? value : "");

const normalizeModelImageSource = (value) => {
    if (typeof value === "string") return value.trim();
    if (!value || typeof value !== "object") return "";
    const candidate = typeof value.url === "string"
        ? value.url
        : (typeof value.path === "string" ? value.path : "");
    return candidate.trim();
};

const clampCanvasSize = (value, fallback) => {
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0) return fallback;
    return Math.max(1, Math.floor(n));
};

export function createSignatureFieldComponent() {
    return {
        name: "SignatureField",
        props: {
            modelValue: {
                type: [String, Object],
                default: "",
            },
            disabled: {
                type: Boolean,
                default: false,
            },
            placeholder: {
                type: String,
                default: "请在此处手写签名",
            },
        },
        emits: ["update:modelValue", "change"],
        data() {
            return {
                ctx: null,
                isDrawing: false,
                hasDrawn: false,
                lastPoint: null,
                activePointerId: null,
                resizeObserver: null,
                resizeTimer: 0,
                lastEmittedValue: "",
            };
        },
        watch: {
            modelValue(newValue) {
                this.syncFromModel(newValue);
            },
        },
        mounted() {
            this.setupCanvas();
            this.syncFromModel(this.modelValue);
            this.bindResizeObserver();
        },
        beforeUnmount() {
            this.cleanupResizeWatcher();
        },
        methods: {
            bindResizeObserver() {
                if (typeof ResizeObserver !== "undefined") {
                    this.resizeObserver = new ResizeObserver(() => {
                        this.scheduleResize();
                    });
                    if (this.$el) {
                        this.resizeObserver.observe(this.$el);
                    }
                    return;
                }
                window.addEventListener("resize", this.scheduleResize);
            },
            cleanupResizeWatcher() {
                if (this.resizeTimer) {
                    clearTimeout(this.resizeTimer);
                    this.resizeTimer = 0;
                }
                if (this.resizeObserver) {
                    this.resizeObserver.disconnect();
                    this.resizeObserver = null;
                } else {
                    window.removeEventListener("resize", this.scheduleResize);
                }
            },
            setupCanvas() {
                const canvas = this.$refs.canvas;
                if (!canvas) return;
                const ctx = canvas.getContext("2d");
                if (!ctx) return;
                this.ctx = ctx;
                this.resizeCanvasAndRestore(true);
            },
            scheduleResize() {
                if (this.resizeTimer) {
                    clearTimeout(this.resizeTimer);
                }
                this.resizeTimer = window.setTimeout(() => {
                    this.resizeTimer = 0;
                    this.resizeCanvasAndRestore(false);
                }, 60);
            },
            resizeCanvasAndRestore(initial = false) {
                const canvas = this.$refs.canvas;
                if (!canvas) return;

                const rect = canvas.getBoundingClientRect();
                const width = clampCanvasSize(rect.width, DEFAULT_CANVAS_WIDTH);
                const height = clampCanvasSize(rect.height, DEFAULT_CANVAS_HEIGHT);
                const ratio = Math.max(window.devicePixelRatio || 1, 1);

                const restoreValue = initial
                    ? normalizeModelImageSource(this.modelValue)
                    : (this.hasDrawn ? this.exportImage() : normalizeModelImageSource(this.modelValue));

                canvas.width = Math.max(1, Math.floor(width * ratio));
                canvas.height = Math.max(1, Math.floor(height * ratio));

                const ctx = canvas.getContext("2d");
                if (!ctx) return;
                this.ctx = ctx;
                this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
                this.ctx.lineCap = "round";
                this.ctx.lineJoin = "round";
                this.ctx.strokeStyle = STROKE_COLOR;
                this.ctx.lineWidth = STROKE_WIDTH;

                this.clearCanvas();
                if (restoreValue) {
                    this.renderFromDataUrl(restoreValue);
                } else {
                    this.hasDrawn = false;
                }
            },
            clearCanvas() {
                const canvas = this.$refs.canvas;
                if (!canvas || !this.ctx) return;
                const width = clampCanvasSize(canvas.clientWidth, DEFAULT_CANVAS_WIDTH);
                const height = clampCanvasSize(canvas.clientHeight, DEFAULT_CANVAS_HEIGHT);
                this.ctx.clearRect(0, 0, width, height);
            },
            getPoint(event) {
                const canvas = this.$refs.canvas;
                if (!canvas) return null;
                const rect = canvas.getBoundingClientRect();
                return {
                    x: event.clientX - rect.left,
                    y: event.clientY - rect.top,
                };
            },
            drawDot(point) {
                if (!this.ctx || !point) return;
                this.ctx.beginPath();
                this.ctx.moveTo(point.x, point.y);
                this.ctx.lineTo(point.x + 0.01, point.y + 0.01);
                this.ctx.stroke();
                this.ctx.closePath();
            },
            drawSegment(from, to) {
                if (!this.ctx || !from || !to) return;
                this.ctx.beginPath();
                this.ctx.moveTo(from.x, from.y);
                this.ctx.lineTo(to.x, to.y);
                this.ctx.stroke();
                this.ctx.closePath();
            },
            exportImage() {
                const canvas = this.$refs.canvas;
                if (!canvas || !this.hasDrawn) return "";
                try {
                    return canvas.toDataURL("image/png");
                } catch {
                    return "";
                }
            },
            emitValue(value) {
                const normalized = normalizeString(value);
                this.lastEmittedValue = normalized;
                this.$emit("update:modelValue", normalized);
                this.$emit("change", normalized);
            },
            syncFromModel(value) {
                const normalized = normalizeModelImageSource(value);
                if (normalized && normalized === this.lastEmittedValue) {
                    this.lastEmittedValue = "";
                    return;
                }
                if (!this.ctx) {
                    this.$nextTick(() => {
                        this.setupCanvas();
                        this.renderFromDataUrl(normalized);
                    });
                    return;
                }
                this.renderFromDataUrl(normalized);
            },
            renderFromDataUrl(dataUrl) {
                const normalized = normalizeString(dataUrl).trim();
                if (!this.ctx) return;
                if (!normalized) {
                    this.clearCanvas();
                    this.hasDrawn = false;
                    return;
                }

                const image = new Image();
                image.onload = () => {
                    const canvas = this.$refs.canvas;
                    if (!canvas || !this.ctx) return;

                    const drawWidth = clampCanvasSize(canvas.clientWidth, DEFAULT_CANVAS_WIDTH);
                    const drawHeight = clampCanvasSize(canvas.clientHeight, DEFAULT_CANVAS_HEIGHT);

                    this.clearCanvas();

                    const ratio = Math.min(
                        drawWidth / Math.max(image.width, 1),
                        drawHeight / Math.max(image.height, 1),
                    );
                    const targetWidth = Math.max(1, image.width * ratio);
                    const targetHeight = Math.max(1, image.height * ratio);
                    const offsetX = (drawWidth - targetWidth) / 2;
                    const offsetY = (drawHeight - targetHeight) / 2;

                    this.ctx.drawImage(image, offsetX, offsetY, targetWidth, targetHeight);
                    this.hasDrawn = true;
                };
                image.onerror = () => {
                    this.clearCanvas();
                    this.hasDrawn = false;
                };
                image.src = normalized;
            },
            onPointerDown(event) {
                if (this.disabled) return;
                if (!this.ctx) this.setupCanvas();
                if (!this.ctx) return;

                const point = this.getPoint(event);
                if (!point) return;

                event.preventDefault();
                const canvas = this.$refs.canvas;
                canvas?.setPointerCapture?.(event.pointerId);

                this.activePointerId = event.pointerId;
                this.isDrawing = true;
                this.lastPoint = point;
                this.drawDot(point);
                this.hasDrawn = true;
            },
            onPointerMove(event) {
                if (!this.isDrawing || this.disabled) return;
                if (this.activePointerId !== null && event.pointerId !== this.activePointerId) return;

                const point = this.getPoint(event);
                if (!point) return;

                event.preventDefault();
                this.drawSegment(this.lastPoint, point);
                this.lastPoint = point;
                this.hasDrawn = true;
            },
            onPointerUp(event) {
                if (!this.isDrawing) return;
                if (this.activePointerId !== null && event.pointerId !== this.activePointerId) return;

                const canvas = this.$refs.canvas;
                canvas?.releasePointerCapture?.(event.pointerId);

                this.isDrawing = false;
                this.activePointerId = null;
                this.lastPoint = null;

                const value = this.exportImage();
                this.emitValue(value);
            },
            clearSignature() {
                if (this.disabled) return;
                this.isDrawing = false;
                this.activePointerId = null;
                this.lastPoint = null;
                this.clearCanvas();
                this.hasDrawn = false;
                this.emitValue("");
            },
        },
        template: `
            <div class="fd-signature" :class="{ 'is-disabled': disabled }">
                <canvas
                    ref="canvas"
                    class="fd-signature-canvas"
                    @pointerdown="onPointerDown"
                    @pointermove="onPointerMove"
                    @pointerup="onPointerUp"
                    @pointerleave="onPointerUp"
                    @pointercancel="onPointerUp"></canvas>
                <div v-if="!hasDrawn" class="fd-signature-placeholder">[[ placeholder ]]</div>
                <div class="fd-signature-actions" v-if="!disabled">
                    <el-button size="small" @click="clearSignature">清空签名</el-button>
                </div>
            </div>
        `,
    };
}
