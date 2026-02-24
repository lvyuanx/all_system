(function(){

    function animateClose(overlay, refresh = false) {
        if (!overlay) return;

        const content = overlay.querySelector("div");

        overlay.style.background = "rgba(0,0,0,0)";
        content.style.transform = "scale(0.8)";
        content.style.opacity = "0";

        setTimeout(() => {
            overlay.remove();
             if (refresh) {
                window.location.reload();
            }
        }, 300);   // 要和 transition 时间一致
    }

    window.showModal = function({url, width='80vw', height='80vh', headerBg='#fff'}){
        if(!url) return;

        const old = document.getElementById("custom-modal");
        if(old) old.remove();

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
        close.style.cursor = "pointer";
        close.style.fontSize = "24px";
        close.style.fontWeight = "bold";

        function closeModal() {
            animateClose(overlay);
        }

        close.onclick = closeModal;

        header.appendChild(close);
        content.appendChild(header);

        const iframe = document.createElement("iframe");
        iframe.src = url;
        iframe.style.border = "none";
        iframe.style.width = "100%";
        iframe.style.height = `calc(100% - 40px)`;
        content.appendChild(iframe);

        overlay.appendChild(content);
        document.body.appendChild(overlay);

        setTimeout(() => {
            overlay.style.background = "rgba(0,0,0,0.5)";
            content.style.transform = "scale(1)";
            content.style.opacity = "1";
        }, 10);

        overlay.addEventListener("click", function(e){
            if(e.target === overlay) closeModal();
        });

        return closeModal;
    };


    window.closeCustomModal = function(refresh = false) {
        const overlay = document.getElementById("custom-modal");
        animateClose(overlay, refresh);
    };

})();