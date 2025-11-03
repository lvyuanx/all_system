(function() {
    function addLogoutButton() {
        const hgroup = document.querySelector("hgroup.main");
        if (!hgroup) return false;

        // 防止重复添加
        if (hgroup.querySelector(".logout-btn")) return true;

        // 创建按钮容器（右侧区域）
        const rightBox = document.createElement("div");
        rightBox.style.marginLeft = "auto";
        rightBox.style.display = "flex";
        rightBox.style.alignItems = "center";

        // 创建退出按钮（使用图标表情）
        const logoutBtn = document.createElement("button");
        logoutBtn.innerHTML = "🚶‍♂️"; // 图标表情
        logoutBtn.title = "退出登录"; // 鼠标悬停提示
        logoutBtn.className = "logout-btn";
        logoutBtn.style.padding = "6px 10px";
        logoutBtn.style.fontSize = "18px";
        logoutBtn.style.border = "none";
        logoutBtn.style.borderRadius = "6px";
        logoutBtn.style.background = "transparent";
        logoutBtn.style.cursor = "pointer";
        logoutBtn.style.transition = "transform 0.2s, background 0.3s";
        logoutBtn.style.marginLeft = "20px";
        logoutBtn.onmouseover = () => {
            logoutBtn.style.background = "rgba(244, 67, 54, 0.15)";
            logoutBtn.style.transform = "scale(1.1)";
        };
        logoutBtn.onmouseout = () => {
            logoutBtn.style.background = "transparent";
            logoutBtn.style.transform = "scale(1)";
        };
        logoutBtn.type = "button";

        // 点击事件：退出登录
        logoutBtn.addEventListener("click", function() {
            window.location.href = "/docs_logout";
        });

        // 把按钮放进右侧容器
        rightBox.appendChild(logoutBtn);

        // 设置 hgroup 为左右布局
        hgroup.style.display = "flex";
        hgroup.style.alignItems = "center";
        hgroup.style.justifyContent = "space-between";

        // 把按钮容器放到 hgroup 内部
        hgroup.appendChild(rightBox);

        return true;
    }

    // 尝试立即添加
    if (!addLogoutButton()) {
        const observer = new MutationObserver(() => {
            if (addLogoutButton()) observer.disconnect();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
})();
