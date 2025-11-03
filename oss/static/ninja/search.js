(function() {
    /**
     * 在 hgroup.main 右侧注入一个搜索框，用于过滤 Swagger 的接口列表
     * 特性：
     *  - 等待 DOM 渲染 (MutationObserver)
     *  - 防止重复添加
     *  - 支持回车触发、输入节流 (debounce)
     *  - 支持清空按钮
     *  - 搜索匹配：接口 path、summary、description、method、tags 等文本
     *  - 高亮（简单通过添加 background）
     */

    const SEARCH_INPUT_CLASS = "swagger-op-search-input";
    const SEARCH_CONTAINER_CLASS = "swagger-op-search-container";
    const HIGHLIGHT_CLASS = "swagger-op-search-highlight";

    function styleHighlight(el) {
        el.classList.add(HIGHLIGHT_CLASS);
    }
    function clearHighlight(el) {
        el.classList.remove(HIGHLIGHT_CLASS);
    }

    function addSearchBox() {
        const hgroup = document.querySelector("hgroup.main");
        if (!hgroup) return false;

        // 防止重复添加
        if (hgroup.querySelector(`.${SEARCH_INPUT_CLASS}`) || hgroup.querySelector(`.${SEARCH_CONTAINER_CLASS}`)) {
            return true;
        }

        // 创建容器推到右边（与退出按钮同区）
        const container = document.createElement("div");
        container.className = SEARCH_CONTAINER_CLASS;
        container.style.display = "flex";
        container.style.alignItems = "center";
        container.style.marginLeft = "12px"; // 与左侧内容保持间距

        // 搜索输入框
        const input = document.createElement("input");
        input.className = SEARCH_INPUT_CLASS;
        input.type = "search";
        input.placeholder = "搜索接口（path / summary / method）";
        input.style.padding = "6px 10px";
        input.style.fontSize = "13px";
        input.style.border = "1px solid #ccd0d5";
        input.style.borderRadius = "6px";
        input.style.minWidth = "320px";
        input.style.maxWidth = "580px";
        input.style.transition = "box-shadow 0.12s ease";
        input.style.outline = "none";
        input.autocomplete = "off";

        input.addEventListener("focus", () => {
            input.style.boxShadow = "0 4px 10px rgba(0,0,0,0.08)";
        });
        input.addEventListener("blur", () => {
            input.style.boxShadow = "none";
        });

        // 清除按钮
        const clearBtn = document.createElement("button");
        clearBtn.type = "button";
        clearBtn.title = "清除";
        clearBtn.innerHTML = "✖";
        clearBtn.style.marginLeft = "8px";
        clearBtn.style.border = "none";
        clearBtn.style.background = "transparent";
        clearBtn.style.cursor = "pointer";
        clearBtn.style.fontSize = "14px";
        clearBtn.style.padding = "4px";

        // 简单的样式注入（用于高亮被匹配的 opblock）
        injectHighlightStyle();

        // 搜索逻辑（防抖）
        let debounceTimer = null;
        const DEBOUNCE_MS = 220;

        function performSearch(keyword) {
            // 规范化
            const q = (keyword || "").trim().toLowerCase();
            // 常见 swagger operation 容器选择器
            const opSelectors = [
                '[class*="opblock"]',           // swagger-ui v3 / v4 常见
                '[class*="operation"]',         // 其他实现
                '[class*="resource"]',          // 旧 swagger 版本
            ];
            const nodes = document.querySelectorAll(opSelectors.join(','));
            if (!nodes || nodes.length === 0) return;

            nodes.forEach((node) => {
                // 获取文本内容用于匹配（包括 path、method、summary、desc）
                const text = (node.innerText || node.textContent || "").toLowerCase();
                if (!q) {
                    // 空查询：显示全部、移除高亮
                    node.style.display = "";
                    clearHighlight(node);
                    return;
                }
                if (text.indexOf(q) !== -1) {
                    node.style.display = "";
                    styleHighlight(node);
                } else {
                    node.style.display = "none";
                    clearHighlight(node);
                }
            });

            // 如果页面存在折叠/展开的控制（部分 swagger ui 渲染 opblock-summary），
            // 也尝试自动展开匹配项的摘要（尽量兼容，不保证所有实现都能展开）
            // 这里尝试触发点击 opblock-summary 来展开（仅当被隐藏或折叠时）
            document.querySelectorAll('[class*="opblock-summary"]').forEach(summary => {
                const parent = summary.closest('[class*="opblock"]');
                if (!parent) return;
                if (parent.style.display === "none") return; // 不显示就跳过
                const isCollapsed = summary.getAttribute('aria-expanded') === 'false' || summary.classList.contains('is-open') === false;
                if (isCollapsed) {
                    try { summary.click(); } catch(e){ /* ignore */ }
                }
            });
        }

        // 事件绑定：输入 & 回车
        input.addEventListener("input", function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => performSearch(this.value), DEBOUNCE_MS);
        });
        input.addEventListener("keydown", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                clearTimeout(debounceTimer);
                performSearch(this.value);
            }
            if (e.key === "Escape") {
                input.value = "";
                performSearch("");
            }
        });

        // 清空按钮
        clearBtn.addEventListener("click", function() {
            input.value = "";
            performSearch("");
            input.focus();
        });

        // 组合到容器，放到 hgroup 的右侧（保持与退出按钮并列）
        container.appendChild(input);
        container.appendChild(clearBtn);

        // 如果 hgroup 已经有右侧容器（之前插入了 logout），我们把搜索放在同一行右侧（靠近左）
        // 否则创建一个 wrapper 并使用 margin-left:auto 推到右侧
        let wrapper = null;
        // 先尝试查找已经存在的右侧容器（例如 logout 的 rightBox）
        const existingRight = hgroup.querySelector("div[style*='margin-left: auto'], div.right-box, div." + SEARCH_CONTAINER_CLASS);
        if (existingRight) {
            // 插入到 existingRight 的最前面（靠左）
            existingRight.insertBefore(container, existingRight.firstChild);
        } else {
            // 创建一个新的 wrapper 并推到右侧
            wrapper = document.createElement("div");
            wrapper.style.marginLeft = "auto";
            wrapper.style.display = "flex";
            wrapper.style.alignItems = "center";
            // 给 wrapper 一个类，方便以后识别
            wrapper.className = "swagger-right-controls";
            wrapper.appendChild(container);
            // 设置 hgroup 为左右布局
            hgroup.style.display = "flex";
            hgroup.style.alignItems = "center";
            hgroup.style.justifyContent = "space-between";
            hgroup.appendChild(wrapper);
        }

        return true;
    }

    // 插入高亮样式
    function injectHighlightStyle() {
        if (document.getElementById("swagger-op-search-style")) return;
        const style = document.createElement("style");
        style.id = "swagger-op-search-style";
        style.innerHTML = `
            .${HIGHLIGHT_CLASS} {
                transition: background-color 0.18s ease, box-shadow 0.18s ease;
                background-color: rgba(255, 249, 196, 0.8) !important;
                box-shadow: 0 2px 6px rgba(34,34,34,0.06);
            }
            .${SEARCH_INPUT_CLASS}::placeholder { color: #9aa4ad; }
            .${SEARCH_CONTAINER_CLASS} input[type="search"]::-ms-clear { display: none; }
        `;
        document.head.appendChild(style);
    }

    // 尝试立即添加
    if (!addSearchBox()) {
        // 监听 DOM 变化，直到插入成功再断开 observer
        const observer = new MutationObserver(() => {
            if (addSearchBox()) observer.disconnect();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

})();
