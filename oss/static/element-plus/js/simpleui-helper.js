(function (global) {

    function getParentVueApp() {
        try {
            if (window.parent && window.parent !== window) {
                if (window.parent.app) {
                    return window.parent.app; // simpleui 根 Vue 实例
                }
            }
        } catch (e) {
            console.warn('无法访问父页面', e);
        }
        return null;
    }

    function getParentElementPlus() {
        try {
            if (window.parent && window.parent !== window) {
                if (window.parent.ElementPlus) {
                    return window.parent.ElementPlus;
                }
            }
        } catch (e) {
            console.warn('无法访问父页面 ElementPlus', e);
        }
        return global.ElementPlus || null;
    }

    // ---------------------------
    // Element Plus 的 ElMessage 封装
    // ---------------------------
    const ElMessage = (options) => {
        const parentApp = getParentVueApp();
        if (parentApp?.$message) {
            return parentApp.$message(options);
        } else if (getParentElementPlus()?.ElMessage) {
            return getParentElementPlus().ElMessage(options);
        } else {
            alert(typeof options === 'string' ? options : options.message);
        }
    };

    ['success', 'warning', 'info', 'error'].forEach(type => {
        ElMessage[type] = (message, opts = {}) => {
            return ElMessage(Object.assign({}, opts, { message, type }));
        };
    });

    // ---------------------------
    // Element Plus 的 ElMessageBox 封装
    // ---------------------------
    const ElMessageBox = {
        alert(message, title = '提示', options = {}) {
            const box = getParentElementPlus()?.ElMessageBox;
            if (box) return box.alert(message, title, options);
            alert(message);
            return Promise.resolve();
        },
        confirm(message, title = '提示', options = {}) {
            const box = getParentElementPlus()?.ElMessageBox;
            if (box) return box.confirm(message, title, options);
            if (confirm(message)) return Promise.resolve();
            return Promise.reject();
        },
        prompt(message, title = '提示', options = {}) {
            const box = getParentElementPlus()?.ElMessageBox;
            if (box) return box.prompt(message, title, options);
            const value = prompt(message);
            if (value !== null) return Promise.resolve({ value });
            return Promise.reject();
        }
    };

    // ---------------------------
    // 额外工具方法
    // ---------------------------
    function goBack() {
        const parentApp = getParentVueApp();
        if (parentApp?.$router) {
            parentApp.$router.back();
        } else {
            window.history.back();
        }
    }

    function refreshParentTab() {
        const parentApp = getParentVueApp();
        if (parentApp?.reload) {
            parentApp.reload();
        } else {
            window.location.reload();
        }
    }

    function closeParentTab() {
        const parentApp = getParentVueApp();
        if (parentApp?.closeCurrentTab) {
            parentApp.closeCurrentTab();
        } else {
            console.warn('父页面不支持关闭标签页功能');
        }
    }

    function openParentTab(url, title) {
        const parentApp = getParentVueApp();
        if (parentApp?.openTab) {
            parentApp.openTab(url, title);
        } else {
            window.open(url, '_blank');
        }
    }

    // 挂载到全局
    global.SimpleUIExtra = {
        ElMessage,
        ElMessageBox,
        goBack,
        refreshParentTab,
        closeParentTab,
        openParentTab
    };

})(window);
