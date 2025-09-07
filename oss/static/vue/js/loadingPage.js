(function(window){
    // 遮罩 DOM
    const mask = document.createElement("div");
    mask.id = "global-loading-mask";
    mask.style.position = "fixed";
    mask.style.top = 0;
    mask.style.left = 0;
    mask.style.width = "100%";
    mask.style.height = "100%";
    mask.style.display = "flex";
    mask.style.flexDirection = "column";
    mask.style.alignItems = "center";
    mask.style.justifyContent = "center";
    mask.style.background = "rgba(255,255,255,1)";
    mask.style.zIndex = 9999;
    mask.style.opacity = 1;
    mask.style.transition = "opacity 0.6s ease";

    // 转圈（更细更小）
    const spinner = document.createElement("div");
    spinner.style.width = "30px";             // 更小
    spinner.style.height = "30px";
    spinner.style.border = "2px solid rgba(0,0,0,0.2)"; // 更细
    spinner.style.borderTopColor = "#409EFF";           // 蓝色
    spinner.style.borderRadius = "50%";
    spinner.style.marginBottom = "6px";        // 间距小
    spinner.style.animation = "loading-spin 1s linear infinite";

    // 文字 + 点点（更小）
    const text = document.createElement("div");
    text.style.color = "#606266";
    text.style.fontSize = "13px";             // 更小
    text.style.fontWeight = "500";
    text.style.display = "flex";
    text.style.alignItems = "center";

    const textNode = document.createElement("span");
    textNode.innerText = "加载中";

    const dots = document.createElement("span");
    dots.style.display = "inline-block";
    dots.style.marginLeft = "2px";
    dots.style.width = "1em";
    dots.style.textAlign = "left";
    dots.style.animation = "loading-dots 1s steps(3,end) infinite";

    text.appendChild(textNode);
    text.appendChild(dots);

    mask.appendChild(spinner);
    mask.appendChild(text);
    document.body.appendChild(mask);

    // keyframes
    const style = document.createElement("style");
    style.innerHTML = `
    @keyframes loading-spin { 0%{transform:rotate(0deg);} 100%{transform:rotate(360deg);} }
    @keyframes loading-dots { 0%{content:'';} 33%{content:'.';} 66%{content:'..';} 100%{content:'...';} }`;
    document.head.appendChild(style);

    // 自动关闭（渐变消失）
    function close(){
        mask.style.opacity = 0;
        setTimeout(()=>mask.remove(), 600);
    }

    window.addEventListener("load", close);

    // 全局控制
    window.Loading = {
        show: function(){
            mask.style.display = "flex";
            mask.style.opacity = 1;
        },
        close: close
    };
})(window);
