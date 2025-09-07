from datetime import datetime, time, timedelta
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.utils.encoding import force_str
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.views.main import ChangeList
from django.urls import path

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


def btn(
    short_description=None, icon=None, type=None, style=None, layer=None, confirm=None
):
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
        if layer:
            func.layer = layer
        if confirm:
            func.confirm = confirm
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
        style="btn-danger",
    )
    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.deleted_at = time_util.now()
            if hasattr(obj, "deleted_by"):
                obj.deleted_by = request.user
            obj.save(
                update_fields=(
                    ["deleted_at", "deleted_by"]
                    if hasattr(obj, "deleted_by")
                    else ["deleted_at"]
                )
            )
        self.message_user(
            request, f"已逻辑删除 {queryset.count()} 项。", messages.SUCCESS
        )


def format_avatar(url: str):

    return format_html(
        "<img src='{}' class='rounded-circle' width='50' height='50' />", url
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


class AuditAdminMixin:
    audit_exclude_fields = (
        "create_user",
        "create_time",
        "update_user",
        "update_time",
        "delete_user",
        "delete_time",
        "is_delete",
    )
    exclude_fields = tuple()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for f in self.audit_exclude_fields:
            if f in form.base_fields:
                form.base_fields.pop(f)
        for f in self.exclude_fields:
            if f in form.base_fields:
                form.base_fields.pop(f)
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_delete=False)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.create_user = request.user
        else:
            obj.update_user = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        from django.utils import timezone

        obj.is_delete = True
        obj.delete_user = request.user
        obj.delete_time = timezone.now()
        obj.save()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)


class CreateTimeQuickFilter(admin.SimpleListFilter):
    title = "创建时间(快捷)"
    parameter_name = "create_time_quick"

    def lookups(self, request, model_admin):
        return (
            ("last_month", "上个月"),
            ("this_month", "本月"),
            ("half_year", "半年内"),
            ("this_year", "今年"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if not v:
            return queryset

        now = time_util.now()  # tz-aware datetime
        today = now.date()  # 当前日期 (date)

        if v == "last_month":
            # 上个月第一天
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1).date()
                end_date = datetime(today.year, 1, 1).date()
            else:
                start_date = datetime(today.year, today.month - 1, 1).date()
                end_date = datetime(today.year, today.month, 1).date()

        elif v == "this_month":
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1).date()
            else:
                end_date = datetime(today.year, today.month + 1, 1).date()

        elif v == "half_year":
            start_date = today - timedelta(days=182)  # 半年前
            end_date = today + timedelta(days=1)

        elif v == "this_year":
            start_date = datetime(today.year, 1, 1).date()
            end_date = datetime(today.year + 1, 1, 1).date()
        else:
            return queryset

        # 转换为 tz-aware datetime，保持和 now 的 tz 一致
        start = datetime.combine(start_date, time.min, tzinfo=now.tzinfo)
        end = datetime.combine(end_date, time.min, tzinfo=now.tzinfo)

        return queryset.filter(create_time__gte=start, create_time__lt=end)


from django.contrib.admin.views.main import ChangeList
from django.urls import path
from django.db.models import Q


class FilteredChangeList(ChangeList):
    """
    通用 ChangeList，支持 /filter/ 路径下启用 get_filter_queryset
    并兼容 search_fields 搜索
    """

    def get_queryset(self, request):
        # 获取基础 queryset
        qs = super().get_queryset(request)

        # 只在 _filter URL 下启用自定义过滤
        if hasattr(self.model_admin, "get_filter_queryset") and getattr(
            request.resolver_match, "url_name", ""
        ).endswith("_filter"):
            # 自定义过滤
            qs = self.model_admin.get_filter_queryset(qs, request)

            # 兼容 search_fields
            search_query = request.GET.get('q', '').strip()
            if search_query and hasattr(self.model_admin, 'get_search_results'):
                qs, _ = self.model_admin.get_search_results(request, qs, search_query)

        return qs

    def get_results(self, request):
        """
        确保 full_result_count 使用过滤后的 queryset
        """
        super().get_results(request)
        if hasattr(self.model_admin, "get_filter_queryset") and getattr(
            request.resolver_match, "url_name", ""
        ).endswith("_filter"):
            qs = self.model_admin.get_filter_queryset(self.queryset.all(), request)

            # 兼容 search_fields
            search_query = request.GET.get('q', '').strip()
            if search_query and hasattr(self.model_admin, 'get_search_results'):
                qs, _ = self.model_admin.get_search_results(request, qs, search_query)

            self.full_result_count = qs.count()
            self.result_list = list(qs)


class FilterChangeListMixin:
    """
    通用 Mixin：支持 /filter/ URL 下启用过滤逻辑，并保留搜索条件
    """

    filter_url_name_suffix = "_filter"
    skip_filter_fields = []

    def get_filter_queryset(self, qs, request):
        """
        支持多参数、多值过滤，并跳过 q 搜索参数
        """
        skip_keys = set(getattr(self, "skip_filter_fields", [])) | {"q"}

        for key in request.GET.keys():
            if key in skip_keys:
                continue

            values = request.GET.getlist(key)
            if not values:
                continue

            if "__" in key and not key.endswith("__in"):
                # 多值用 Q 对象 OR 连接
                if len(values) == 1:
                    qs = qs.filter(**{key: values[0]})
                else:
                    q_obj = Q()
                    for v in values:
                        q_obj |= Q(**{key: v})
                    qs = qs.filter(q_obj)
            else:
                # 普通字段使用 __in
                if len(values) == 1:
                    qs = qs.filter(**{key: values[0]})
                else:
                    qs = qs.filter(**{f"{key}__in": values})

        # search_fields 逻辑
        search_query = request.GET.get('q', '').strip()
        if search_query and hasattr(self, 'get_search_results'):
            qs, _ = self.get_search_results(request, qs, search_query)

        return qs

    def get_changelist(self, request, **kwargs):
        return FilteredChangeList

    def get_urls(self):
        """
        增加 /filter/ 自定义 URL
        """
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            path(
                "filter/",
                self.admin_site.admin_view(self.changelist_view),
                name=f"{info[0]}_{info[1]}{self.filter_url_name_suffix}",
            )
        ]
        return custom_urls + urls

    # def changelist_view(self, request, extra_context=None):
    #     """
    #     方案B：保留 /filter/ URL 下的原有 GET 参数，
    #     搜索表单提交也会保留多参数过滤条件
    #     """
    #     return super().changelist_view(request, extra_context)




class OperateButtonsMixin:
    """
    Django Admin list_display 多按钮列 Mixin
    - 支持 Element UI 风格按钮
    - 配置按钮名称、类型、模式（跳转/弹窗）、URL 或 JS 函数
    使用方法：
        operate_buttons_config = [
            {
                "name": "编辑",
                "type": "primary",        # default / primary / warning / danger
                "mode": "link",           # link / modal
                "url": lambda obj: reverse("admin:app_model_change", args=[obj.pk]),
                "icon": "el-icon-edit",   # 可选
            },
            {
                "name": "弹窗",
                "type": "text",
                "mode": "modal",
                "url": lambda obj: reverse("admin:app_model_change", args=[obj.pk]),
            }
        ]
    """

    operate_buttons_config = []  # 子类定义按钮配置

    def operate_buttons(self, obj):
        buttons = []

        for conf in getattr(self, "operate_buttons_config", []):
            label = conf.get("name", "按钮")
            btn_type = conf.get(
                "type", "default"
            )  # default / primary / warning / danger / text
            mode = conf.get("mode", "link")  # link / modal
            icon = conf.get("icon", "")
            url_func = conf.get("url")
            js_func = conf.get("js")  # 自定义 JS 函数调用
            modal_width = conf.get("modal_width")
            modal_height = conf.get("modal_height")

            # 解析 URL
            if callable(url_func):
                url = url_func(obj)
            else:
                url = url_func or "#"

            # Element UI 按钮 class
            btn_class = {
                "primary": "el-button el-button--primary",
                "warning": "el-button el-button--warning",
                "danger": "el-button el-button--danger",
                "text": "el-button el-button--text",
                "default": "el-button el-button--default",
            }.get(btn_type, "el-button el-button--default")

            # 按钮 HTML
            if mode == "modal":
                btn_html = format_html(
                    """
                        <button type="button" class="{}"
                            onclick="showModal({{url: '{}', width: '{}', height: '{}'}})">
                            {}<span>{}</span>
                        </button>
                    """,
                    btn_class,
                    url,
                    modal_width,
                    modal_height,
                    format_html('<i class="{}"></i>', icon) if icon else "",
                    label,
                )

            elif mode == "js" and js_func:
                btn_html = format_html(
                    """
                    <button type="button" class="{}" onclick="{}(event, {})">
                        {}<span>{}</span>
                    </button>
                """,
                    btn_class,
                    js_func,
                    obj.pk,
                    format_html('<i class="{}"></i>', icon) if icon else "",
                    label,
                )
            else:
                # 默认跳转
                btn_html = format_html(
                    """
                    <button type="button" class="{}" onclick="window.location.href='{}'">
                        {}<span>{}</span>
                    </button>
                """,
                    btn_class,
                    url,
                    format_html('<i class="{}"></i>', icon) if icon else "",
                    label,
                )

            buttons.append(btn_html)

        # 返回所有按钮 HTML
        return format_html_join(" ", "{}", ((btn,) for btn in buttons))

    operate_buttons.short_description = "操作"
    operate_buttons.allow_tags = True
    


