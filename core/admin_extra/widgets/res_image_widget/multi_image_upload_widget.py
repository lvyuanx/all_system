import json
from django import forms
from django.template import Context, Engine
from django.utils.safestring import mark_safe
from ..base_widget import BaseWidget


class MultiImageUploadWidget(BaseWidget):
    """多图片上传控件"""

    html_name = "multi_image_upload_widget.html"

    def render(self, name, value, attrs=None, renderer=None):
        widget_conf = self.attrs.get("widget_conf", {})
        value_attr = widget_conf.get("value_attr_name", name)

        # 将值转换为 JSON 字符串
        value = self.attrs.get(value_attr, "[]")
        if isinstance(value, list):
            value = json.dumps(value, ensure_ascii=False)

        engine = Engine(debug=False)
        template = engine.from_string(self.widget_html)

        context = self.attrs.get("context", {})
        context.update({
            "widget_val": value,
            "file_field_name": name,
        })

        html_rendered = template.render(Context(context))
        return mark_safe(html_rendered)
