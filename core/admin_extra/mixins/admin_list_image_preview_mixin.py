# -*-coding:utf-8 -*-

"""
# File       : admin_list_image_preview_mixin.py
# Time       : 2025-09-08 10:44:38
# Author     : lyx
# version    : python 3.11
# Description: admin 列表页，图片预览
"""

class AdminListImagePreviewMixin:
    image_preview = {}  # 形式：{"字段名": "列名"}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        def make_preview_func(field_name, column_title):
            def preview_func(self, obj):
                img_field = getattr(obj, field_name)
                if img_field and hasattr(img_field, "url"):
                    return cls.format_image_lightbox(img_field.url, field_name)
                return ""

            preview_func.short_description = (
                column_title or field_name.replace("_", " ").title()
            )
            preview_func.allow_tags = True
            return preview_func

        for field, title in cls.image_preview.items():
            method_name = f"{field}_preview"
            setattr(cls, method_name, make_preview_func(field, title))

    @staticmethod
    def format_image_lightbox(
        url,
        field_name,
        thumb_width=40,
        thumb_height=40,
        style="border-radius: 25%; cursor: pointer; vertical-align: middle;",
    ):
        from django.utils.safestring import mark_safe

        html = f"""
            <img 
                src="{url}" 
                width="{thumb_width}" height="{thumb_height}" 
                style="{style}"
                class="admin-lightbox-thumb"
                data-full-url="{url}"
                alt="点击查看大图"
                title="点击查看大图"
            />

            <style>
                .admin-lightbox-overlay {{
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.8);
                    z-index: 9999;
                    display: none;
                    justify-content: center;
                    align-items: center;
                }}
                .admin-lightbox-overlay img {{
                    max-width: 90%;
                    max-height: 90%;
                    box-shadow: 0 0 20px rgba(255,255,255,0.5);
                    border-radius: 8px;
                }}
                .admin-lightbox-close {{
                    display: none;
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    background: rgba(255,255,255,0.8);
                    border: none;
                    font-size: 28px;
                    font-weight: bold;
                    color: #333;
                    width: 40px;
                    height: 40px;
                    border-radius: 20px;
                    cursor: pointer;
                    line-height: 30px;
                    text-align: center;
                    user-select: none;
                    transition: background-color 0.3s ease;
                }}
                .admin-lightbox-close:hover {{
                    background: #ff4d4f;
                    color: white;
                }}
            </style>

            <script>
            (function() {{
                if (window._adminLightboxInitialized) return;
                window._adminLightboxInitialized = true;

                var overlay = document.createElement("div");
                overlay.className = "admin-lightbox-overlay";
                overlay.id = "admin-lightbox-overlay";

                var imgPreview = document.createElement("img");
                overlay.appendChild(imgPreview);

                var closeBtn = document.createElement("button");
                closeBtn.className = "admin-lightbox-close";
                closeBtn.id = "admin-lightbox-close";
                closeBtn.innerText = "\\u00D7";
                closeBtn.title = "关闭预览";

                function closeLightbox() {{
                    overlay.style.display = "none";
                    closeBtn.style.display = "none";
                    imgPreview.src = "";
                }}

                overlay.addEventListener("click", function(e) {{
                    if (e.target === overlay) {{
                        closeLightbox();
                    }}
                }});

                closeBtn.addEventListener("click", closeLightbox);

                document.body.appendChild(overlay);
                document.body.appendChild(closeBtn);

                document.addEventListener("click", function(e) {{
                    var target = e.target;
                    if (target.classList.contains("admin-lightbox-thumb")) {{
                        var fullUrl = target.getAttribute("data-full-url");
                        if (!fullUrl) return;

                        imgPreview.src = fullUrl;
                        overlay.style.display = "flex";
                        closeBtn.style.display = "block";
                    }}
                }});
            }})();
            </script>
        """
        return mark_safe(html)