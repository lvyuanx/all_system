from django import forms
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.utils.encoding import force_str
from django.contrib.contenttypes.models import ContentType

from core.utils import time_util



class AdminFormImageUpload(forms.ModelForm):
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

        css_style = '''<style>
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
        </style>'''

        js_script = '''<script>
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
        </script>'''

        preview_html_template = '''
        <div class="image-wrapper" data-input-id="id_{name}"
             style="width:{width}; height:{height}; margin-top:5px; display:inline-block;">
            <img id="preview-{name}" src="{url}" data-full-url="{url}"
                style="width:100%; height:100%; object-fit:cover; border-radius:8px;" />
            <div class="image-overlay">
                <button type="button" class="preview-btn">预览</button>
                <button type="button" class="upload-btn">上传</button>
            </div>
        </div>
        '''

        for i, (field_name, config) in enumerate(field_config_map.items()):
            if field_name in self.fields:
                instance = getattr(self.instance, field_name, None)
                url = instance.url if instance and hasattr(instance, "url") and instance.url else ""

                width = config.get("width", "100px")
                height = config.get("height", "100px")

                html = preview_html_template.format(name=field_name, url=url, width=width, height=height)
                if i == 0:
                    html += css_style + js_script

                self.fields[field_name].help_text = mark_safe(html)



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
            preview_func.short_description = column_title or field_name.replace("_", " ").title()
            preview_func.allow_tags = True
            return preview_func

        for field, title in cls.image_preview.items():
            method_name = f"{field}_preview"
            setattr(cls, method_name, make_preview_func(field, title))

    @staticmethod
    def format_image_lightbox(url, field_name, thumb_width=40, thumb_height=40, style="border-radius: 25%; cursor: pointer; vertical-align: middle;"):
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


class OperateBtnAdminMixin:
    """
    Django Admin 操作按钮通用 Mixin
    支持：
    - 按钮跳转到新页面 / 弹出模态框
    - 按钮样式（default / primary / warning / danger）
    - 确认提示
    - 模态框宽高可配置：modal_width, modal_height
    """

    operate_btn_dict = {}

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = []

        for btn_key, conf in self.operate_btn_dict.items():
            view_func = conf.get("onclick")
            if not view_func:
                continue

            url_name = f"{self.model._meta.app_label}_{self.model._meta.model_name}_{btn_key}"

            def make_view(func):
                def view(request, pk, func=func):
                    obj = get_object_or_404(self.model, pk=pk)
                    return func(self, request, obj)

                return self.admin_site.admin_view(view)

            custom_urls.append(
                path(f"{btn_key}/<int:pk>/", make_view(view_func), name=url_name)
            )

        return custom_urls + urls

    def operator_buttons(self, obj):
        buttons = []
        for btn_key, conf in self.operate_btn_dict.items():
            label = conf.get("name", btn_key)
            confirm_text = conf.get("confirm", {}).get("text", "")
            btn_type = conf.get("type", "default")  # default / primary / warning / danger
            mode = conf.get("mode", "normal")  # normal / modal
            modal_width = conf.get("modal_width", "80vw")
            modal_height = conf.get("modal_height", "80vh")
            extra_url = conf.get("url")  # 自定义 URL

            if extra_url:
                url = extra_url(obj) if callable(extra_url) else extra_url
            else:
                url = reverse(
                    f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_{btn_key}",
                    args=[obj.pk]
                )

            onclick = ""
            if confirm_text:
                onclick += f"if(!confirm('{confirm_text}')) return false;"

            # 取消原来根据 mode == modal 加 return false 的行为，改由 data-mode 控制

            btn_class = self.get_button_css_class(btn_type)

            btn_html = format_html(
                '<a class="button {}" href="{}" onclick="{}" '
                'data-modal-width="{}" data-modal-height="{}" data-label="{}" data-mode="{}">{}</a>',
                btn_class, url, onclick, modal_width, modal_height, label, mode, label
            )
            buttons.append(btn_html)

        return format_html_join(' ', '{}', ((btn,) for btn in buttons)) + self.modal_script()

    operator_buttons.short_description = "操作"
    operator_buttons.allow_tags = True

    @staticmethod
    def get_button_css_class(btn_type):
        return {
            "primary": "btn-primary",
            "warning": "btn-warning",
            "danger": "btn-danger",
        }.get(btn_type, "btn-default")

    def modal_script(self):
        return mark_safe("""
            <style>
                .modal-overlay {
                    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0, 0, 0, 0.5); z-index: 1000;
                    display: flex; justify-content: center; align-items: center;
                }
                .modal-content {
                    background: #fff; padding: 0; border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    position: relative;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    z-index: 1001;
                }
                .modal-content iframe {
                    flex-grow: 1;
                    border: none;
                    width: 100%;
                    height: 100%;
                }
                .modal-close {
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    cursor: pointer;
                    font-size: 20px;
                    font-weight: bold;
                    background: #f44336;
                    color: white;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    line-height: 40px;
                    text-align: center;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    user-select: none;
                    transition: background 0.3s ease;
                    z-index: 1100;
                }
                .modal-close:hover {
                    background: #d32f2f;
                }
            </style>
            <script>
                function showModal(title, url, width = '80vw', height = '80vh') {
                    const old = document.getElementById("custom-modal");
                    if (old) old.remove();

                    const overlay = document.createElement("div");
                    overlay.className = "modal-overlay";
                    overlay.id = "custom-modal";

                    const content = document.createElement("div");
                    content.className = "modal-content";
                    content.style.width = width;
                    content.style.height = height;

                    const iframe = document.createElement("iframe");
                    iframe.src = url;

                    const close = document.createElement("div");
                    close.className = "modal-close";
                    close.innerHTML = "&times;";
                    close.title = "关闭";
                    close.onclick = () => overlay.remove();

                    content.appendChild(iframe);
                    overlay.appendChild(content);
                    overlay.appendChild(close);

                    // 点击遮罩层关闭模态框（但点击内容区不关闭）
                    overlay.addEventListener('click', function(e) {
                        if (e.target === overlay) {
                            overlay.remove();
                        }
                    });

                    document.body.appendChild(overlay);
                }

                document.addEventListener("DOMContentLoaded", function () {
                    document.querySelectorAll(".button").forEach(btn => {
                        btn.addEventListener("click", function (e) {
                            const label = btn.dataset.label || "";
                            const url = btn.getAttribute("href");
                            const width = btn.dataset.modalWidth || "80vw";
                            const height = btn.dataset.modalHeight || "80vh";
                            const mode = btn.dataset.mode || "normal";

                            if (mode === "modal") {
                                e.preventDefault();
                                showModal(label, url, width, height);
                            }
                        });
                    });
                });
            </script>
        """)





def btn(short_description=None, icon=None, type=None, style=None):
    """
    用于简化 Django Admin Action 按钮属性设置的装饰器（支持 SimpleUI 样式）
    """
    def decorator(func):
        if short_description:
            func.short_description = short_description
        if icon:
            func.icon = icon
        if type:
            func.type = type
        if style:
            func.style = style
        return func
    return decorator


class SoftDeleteAdmin:
    """
    用于逻辑删除的通用 Admin 基类：
    - 自动过滤 deleted_at 不为空的记录
    - 禁用默认删除按钮
    - 提供逻辑删除动作
    """
    actions = ["soft_delete_selected"]

    def get_queryset(self, request):
        # 使用自定义 objects 管理器（默认只查未逻辑删除的）
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    def has_delete_permission(self, request, obj=None):
        # 禁用默认物理删除按钮
        return False
    
    @btn(
        short_description=" 逻辑删除", 
        icon="fa fa-trash",
        type="danger",
        style="btn-danger"
    )
    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.deleted_at = time_util.now()
            if hasattr(obj, "deleted_by"):
                obj.deleted_by = request.user
            obj.save(update_fields=["deleted_at", "deleted_by"] if hasattr(obj, "deleted_by") else ["deleted_at"])
        self.message_user(request, f"已逻辑删除 {queryset.count()} 项。", messages.SUCCESS)


def format_avatar(url: str):

    return format_html(
        "<img src='{}' class='rounded-circle' width='50' height='50' />",
        url
    )
    


def log_custom_action(request, obj, msg="执行了自定义操作", action_flag=CHANGE):
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=force_str(obj),
        action_flag=action_flag,
        change_message=msg,
    )