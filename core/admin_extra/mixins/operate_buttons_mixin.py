# -*-coding:utf-8 -*-

"""
# File       : operate_buttons_mixin.py
# Time       : 2025-09-08 10:40:51
# Author     : lyx
# version    : python 3.11
# Description: 操作列添加按钮
"""
import json

from django.utils.html import format_html, format_html_join

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

        cfg = []
        if hasattr(self, "get_operate_buttons_config"):
            cfg = getattr(self, "get_operate_buttons_config")(obj)
        elif hasattr(self, "operate_buttons_config"):
            cfg = self.operate_buttons_config

        for conf in cfg:
            label = conf.get("name", "按钮")
            btn_type = conf.get(
                "type", "default"
            )  # default / primary / warning / danger / text
            mode = conf.get("mode", "link")  # link / modal / js
            icon = conf.get("icon", "")
            url_func = conf.get("url")
            js_func = conf.get("js_func")  # 自定义 JS 函数调用
            modal_width = conf.get("modal_width")
            modal_height = conf.get("modal_height")
            confirm_text = str(conf.get("confirm") or "").strip()
            confirm_title = str(conf.get("confirm_title") or "操作确认").strip()
            confirm_type = str(conf.get("confirm_type") or "warning").strip() or "warning"

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

            def wrap_confirm(action_js: str) -> str:
                if not confirm_text:
                    return action_js
                msg = json.dumps(confirm_text)
                title = json.dumps(confirm_title)
                ctype = json.dumps(confirm_type)
                return (
                    "(function(){"
                    "var _do=function(){" + action_js + "};"
                    "var _box=(window.SimpleUIExtra&&window.SimpleUIExtra.ElMessageBox)||null;"
                    "if(_box&&typeof _box.confirm==='function'){"
                    f"_box.confirm({msg},{title},{{type:{ctype},confirmButtonText:'确认',cancelButtonText:'取消'}})"
                    ".then(function(){_do();}).catch(function(){});"
                    f"}}else if(window.confirm({msg})){{_do();}}"
                    "})();"
                )

            # 按钮 HTML
            if mode == "modal":
                modal_call = "showModal({url: %s, width: %s, height: %s})" % (
                    json.dumps(str(url)),
                    json.dumps(str(modal_width or "")),
                    json.dumps(str(modal_height or "")),
                )
                onclick = wrap_confirm(f"{modal_call};")
                btn_html = format_html(
                    """
                        <button type="button" class="{}"
                            onclick="{}">
                            {}<span>{}</span>
                        </button>
                    """,
                    btn_class,
                    onclick,
                    format_html('<i class="{}"></i>', icon) if icon else "",
                    label,
                )

            elif mode == "js" and js_func:
                js_call = "{}(event, {})".format(js_func, obj.pk)
                onclick = wrap_confirm(f"{js_call};")
                btn_html = format_html(
                    """
                    <button type="button" class="{}" onclick="{}">
                        {}<span>{}</span>
                    </button>
                """,
                    btn_class,
                    onclick,
                    format_html('<i class="{}"></i>', icon) if icon else "",
                    label,
                )
            else:
                # 默认跳转
                jump_call = f"window.location.href={json.dumps(str(url))}"
                onclick = wrap_confirm(f"{jump_call};")
                btn_html = format_html(
                    """
                    <button type="button" class="{}" onclick="{}">
                        {}<span>{}</span>
                    </button>
                """,
                    btn_class,
                    onclick,
                    format_html('<i class="{}"></i>', icon) if icon else "",
                    label,
                )

            buttons.append(btn_html)

        # 返回所有按钮 HTML
        return format_html_join(" ", "{}", ((btn,) for btn in buttons))

    operate_buttons.short_description = "操作"
    operate_buttons.allow_tags = True
    
