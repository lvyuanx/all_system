(function (global) {
    // ---------------------------
    // 获取父 Vue 实例
    // ---------------------------
    function getParentVueApp() {
        try {
            if (window.parent && window.parent !== window) {
                if (window.parent.app && window.parent.app._isVue) {
                    return window.parent.app;
                }
            }
        } catch (e) {
            console.warn("无法访问父页面", e);
        }
        return null;
    }

    // ---------------------------
    // 关闭模态框
    // ---------------------------
    function closeParentModal() {
        try {
            if (window.parent && window.parent !== window) {
                if (window.parent.closeCustomModal) {
                    window.parent.closeCustomModal();
                }
            }
        } catch (e) {
            console.warn("无法访问父页面", e);
        }
    }

    // ---------------------------
    // 获取父页面的 Element 实例（兼容 Vue2 + Vue3）
    // ---------------------------
    function getParentElement() {
        const parentApp = getParentVueApp();

        // Vue2 场景：Element 组件挂在 Vue 实例上
        if (parentApp) {
            const hasMessage = !!parentApp.$message;
            const hasAlert = !!parentApp.$alert;
            const hasConfirm = !!parentApp.$confirm;

            if (hasMessage || hasAlert || hasConfirm) {
                return {
                    ElMessage: parentApp.$message,
                    ElMessageBox: {
                        alert: parentApp.$alert,
                        confirm: parentApp.$confirm,
                        prompt: parentApp.$prompt
                    }
                };
            }
        }

        // Vue3 场景：Element Plus 全局挂载
        if (window.parent && window.parent.ElementPlus) {
            return window.parent.ElementPlus;
        }

        return global.ElementPlus || null;
    }

    // ---------------------------
    // Element 的 ElMessage 封装
    // ---------------------------
    const ElMessage = (options) => {
        const el = getParentElement();
        if (el?.ElMessage) return el.ElMessage(options);
        alert(typeof options === "string" ? options : options.message);
    };

    ['success', 'warning', 'info', 'error'].forEach(type => {
        ElMessage[type] = (message, opts = {}) =>
            ElMessage(Object.assign({}, opts, { message, type }));
    });

    // ---------------------------
    // Element 的 ElMessageBox 封装
    // ---------------------------
    const ElMessageBox = {
        alert(message, title = '提示', options = {}) {
            const el = getParentElement();
            if (el?.ElMessageBox?.alert) return el.ElMessageBox.alert(message, title, options);
            alert(message);
            return Promise.resolve();
        },
        confirm(message, title = '提示', options = {}) {
            const el = getParentElement();
            if (el?.ElMessageBox?.confirm) return el.ElMessageBox.confirm(message, title, options);
            if (confirm(message)) return Promise.resolve();
            return Promise.reject();
        },
        prompt(message, title = '提示', options = {}) {
            const el = getParentElement();
            if (el?.ElMessageBox?.prompt) return el.ElMessageBox.prompt(message, title, options);
            const value = prompt(message);
            if (value !== null) return Promise.resolve({ value });
            return Promise.reject();
        }
    };

    // ---------------------------
    // 页面导航工具
    // ---------------------------
    function goBack() {
        const parentApp = getParentVueApp();
        if (parentApp?.$router) parentApp.$router.back();
        else window.history.back();
    }

    // ---------------------------
    // 打开父页面 Tab / 新标签 / 当前 Tab 跳转
    // ---------------------------
    function openParentTab(url, title = '', mode = 'tab') {
        const parentApp = getParentVueApp();
        const finalTitle = title || document.title || url;

        if (mode === 'tab') {
            if (parentApp?.openTab) {
                parentApp.openTab({
                    url: url,
                    name: finalTitle,
                    eid: new Date().getTime() + "" + Math.random()
                });
            } else {
                window.open(url, '_blank');
            }
        } else if (mode === 'new') {
            window.open(url, '_blank');
        } else if (mode === 'self') {
            if (parentApp?.$router) parentApp.$router.push(url);
            else window.location.href = url;
        } else {
            console.warn(`未知的跳转模式: ${mode}`);
        }
    }

    function navigate(url, title = '', mode = 'tab') {
        openParentTab(url, title, mode);
    }

    global.SimpleUIExtra = {
        ElMessage,
        ElMessageBox,
        closeParentModal,
        goBack,
        openParentTab,
        navigate,
    };
})(window);
