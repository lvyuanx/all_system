import os
from django import forms
from django.template import Context, Engine
from django.utils.safestring import mark_safe
from ..base_widget import BaseWidget


class MultiImageUploadWidget(BaseWidget):
    """多图片上传控件"""

    html_name = "multi_image_upload_widget.html"

    def render(self, name, value, attrs=None, renderer=None):
        """
        name: 字段名
        value: 已有图片列表（逗号分隔 或 list）
        """
        field_value = self.attrs.get("field_value")

        # 渲染 HTML
        engine = Engine(debug=False)
        template = engine.from_string(self.widget_html)
        context = self.attrs.get("context", {})
        context.update({
            "field_value": field_value,
            "field_name": name,
        })
        html_rendered = template.render(Context(context))
        return mark_safe(html_rendered)
