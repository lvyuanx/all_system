# -*-coding:utf-8 -*-

"""
# File       : admin_form_image_upload.py
# Time       : 2025-09-08 10:50:14
# Author     : lyx
# version    : python 3.11
# Description: admin 编辑页面图片上传功能
"""

from django import forms
from django.utils.safestring import mark_safe

class AdminFormImageUploadForm(forms.ModelForm):
    """
    支持图片上传字段预览功能的Admin表单基类。
    """

    # 支持字段：["field1", "field2"] 或 {"field1": {...}, "field2": {...}}
    upload_image_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 兼容字段名列表写法
        if isinstance(self.upload_image_fields, (list, tuple)):
            field_config_map = {name: {} for name in self.upload_image_fields}
        elif isinstance(self.upload_image_fields, dict):
            field_config_map = self.upload_image_fields
        else:
            raise ValueError("upload_image_fields 应为 list、tuple 或 dict 类型")

        css_style = """<style>
          .image-wrapper { position: relative !important; }
          .image-overlay {
            position: absolute !important;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.5) !important;
            border-radius: 8px !important;
            opacity: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            transition: opacity 0.3s ease !important;
            z-index: 9999 !important;
          }
          .image-wrapper:hover .image-overlay {
            opacity: 1 !important;
          }
          .preview-btn, .upload-btn {
            margin: 2px !important;
            padding: 2px 6px !important;
            background: #fff !important;
            border: none !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            font-size: 12px !important;
            user-select: none !important;
          }
        </style>"""

        js_script = """<script>
        document.addEventListener("DOMContentLoaded", function () {
            if (!document.getElementById("admin-image-lightbox-overlay")) {
                const overlay = document.createElement("div");
                overlay.id = "admin-image-lightbox-overlay";
                overlay.style.cssText = "display:none;position:fixed;top:0;left:0;width:100%;height:100%;background-color:rgba(0,0,0,0.8);z-index:10000;justify-content:center;align-items:center;";
                const img = document.createElement("img");
                img.style.maxWidth = "90%";
                img.style.maxHeight = "90%";
                img.style.borderRadius = "10px";
                overlay.appendChild(img);
                const closeBtn = document.createElement("span");
                closeBtn.innerHTML = "&times;";
                closeBtn.style.cssText = "position:absolute;top:20px;right:30px;font-size:40px;font-weight:bold;color:white;cursor:pointer;z-index:10001;";
                overlay.appendChild(closeBtn);
                closeBtn.onclick = () => overlay.style.display = "none";
                overlay.onclick = e => { if (e.target === overlay) overlay.style.display = "none"; };
                document.body.appendChild(overlay);
            }

            document.querySelectorAll(".preview-btn").forEach(btn => {
                btn.addEventListener("click", function (e) {
                    e.preventDefault();
                    const img = document.getElementById("admin-image-lightbox-overlay").querySelector("img");
                    const fullUrl = this.closest(".image-wrapper").querySelector("img").dataset.fullUrl;
                    img.src = fullUrl;
                    document.getElementById("admin-image-lightbox-overlay").style.display = "flex";
                });
            });

            document.querySelectorAll(".upload-btn").forEach(btn => {
                btn.addEventListener("click", function (e) {
                    e.preventDefault();
                    const wrapper = this.closest(".image-wrapper");
                    const inputId = wrapper.dataset.inputId;
                    const input = document.getElementById(inputId);
                    if (input) input.click();
                });
            });

            document.querySelectorAll("input[type='file']").forEach(input => {
                input.addEventListener("change", function () {
                    const preview = document.getElementById("preview-" + this.name);
                    if (this.files.length > 0) {
                        const url = URL.createObjectURL(this.files[0]);
                        preview.src = url;
                        preview.dataset.fullUrl = url;
                    }
                });
            });
        });
        </script>"""

        preview_html_template = """
        <div class="image-wrapper" data-input-id="id_{name}"
             style="width:{width}; height:{height}; margin-top:5px; display:inline-block;">
            <img id="preview-{name}" src="{url}" data-full-url="{url}"
                style="width:100%; height:100%; object-fit:cover; border-radius:8px;" />
            <div class="image-overlay">
                <button type="button" class="preview-btn">预览</button>
                <button type="button" class="upload-btn">上传</button>
            </div>
        </div>
        """

        for i, (field_name, config) in enumerate(field_config_map.items()):
            if field_name in self.fields:
                instance = getattr(self.instance, field_name, None)
                url = (
                    instance.url
                    if instance and hasattr(instance, "url") and instance.url
                    else ""
                )

                width = config.get("width", "100px")
                height = config.get("height", "100px")

                html = preview_html_template.format(
                    name=field_name, url=url, width=width, height=height
                )
                if i == 0:
                    html += css_style + js_script

                self.fields[field_name].help_text = mark_safe(html)