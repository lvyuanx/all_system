(function(){
    /**
     * showModal({url, width, height, headerBg})
     * 打开模态框，并嵌入 iframe，支持自定义头部背景色
     * 返回关闭函数，可在外部或 iframe 内部调用
     */
    window.showModal = function({url, width='80vw', height='80vh', headerBg='#fff'}){
        if(!url) return;

        const old = document.getElementById("custom-modal");
        if(old) old.remove();

        // 遮罩层
        const overlay = document.createElement("div");
        overlay.id = "custom-modal";
        overlay.style.position = "fixed";
        overlay.style.top = 0;
        overlay.style.left = 0;
        overlay.style.right = 0;
        overlay.style.bottom = 0;
        overlay.style.background = "rgba(0,0,0,0)";
        overlay.style.zIndex = 10000;
        overlay.style.display = "flex";
        overlay.style.justifyContent = "center";
        overlay.style.alignItems = "center";
        overlay.style.transition = "background 0.3s ease";

        // 内容容器
        const content = document.createElement("div");
        content.style.background = "#fff";
        content.style.borderRadius = "8px";
        content.style.width = width;
        content.style.height = height;
        content.style.position = "relative";
        content.style.display = "flex";
        content.style.flexDirection = "column";
        content.style.overflow = "hidden";
        content.style.boxShadow = "0 8px 24px rgba(0,0,0,0.3)";
        content.style.transform = "scale(0.8)";
        content.style.opacity = "0";
        content.style.transition = "all 0.3s ease";

        // 头部固定关闭按钮
        const header = document.createElement("div");
        header.style.height = "40px";
        header.style.flexShrink = "0";
        header.style.display = "flex";
        header.style.justifyContent = "flex-end";
        header.style.alignItems = "center";
        header.style.padding = "0 10px";
        header.style.background = headerBg;
        header.style.borderBottom = "1px solid #ddd";

        const close = document.createElement("div");
        close.innerHTML = "&times;";
        close.title = "关闭";
        close.style.cursor = "pointer";
        close.style.fontSize = "24px";
        close.style.fontWeight = "bold";
        close.style.color = "#333";

        // 关闭函数
        function closeModal() {
            overlay.style.background = "rgba(0,0,0,0)";
            content.style.transform = "scale(0.8)";
            content.style.opacity = "0";
            setTimeout(() => overlay.remove(), 300);
        }

        close.onclick = closeModal;
        header.appendChild(close);
        content.appendChild(header);

        // iframe
        const iframe = document.createElement("iframe");
        iframe.src = url;
        iframe.style.border = "none";
        iframe.style.width = "100%";
        iframe.style.height = `calc(100% - 40px)`;
        content.appendChild(iframe);

        overlay.appendChild(content);
        document.body.appendChild(overlay);

        // 打开动画
        setTimeout(() => {
            overlay.style.background = "rgba(0,0,0,0.5)";
            content.style.transform = "scale(1)";
            content.style.opacity = "1";
        }, 10);

        // 点击遮罩关闭
        overlay.addEventListener("click", function(e){
            if(e.target === overlay) closeModal();
        });

        // 返回关闭函数，可在 iframe 内部调用
        return closeModal;
    };

    // 全局注册一个函数，iframe 内部可以通过 parent.closeCustomModal() 关闭
    window.closeCustomModal = function() {
        const overlay = document.getElementById("custom-modal");
        if(overlay) overlay.remove();
    };
})();
