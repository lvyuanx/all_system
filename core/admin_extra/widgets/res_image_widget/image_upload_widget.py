import inspect
import os
from django import forms
from django.template import Context, Engine
from django.utils.safestring import mark_safe
from ..base_widget import BaseWidget


class ImageUploadWidget(BaseWidget):
    """自定义省市区三级联动选择控件"""

    html_name = "image_upload_widget.html"

    def render(self, name, value, attrs=None, renderer=None):
        """
        name: 当前字段名（这里是 linkage）
        attrs: 可以由外部传入的初始值
        """
        # 获取widget组件配置
        widget_conf = self.attrs.get("widget_conf", {})
        value = self.attrs.get(widget_conf["value_attr_name"], "")
        
        # 用 Django 模板引擎渲染 HTML
        engine = Engine(debug=False)
        template = engine.from_string(self.widget_html)
        context = self.attrs.get("context", {})
        context["widget_val"] = value
        context = Context(context)
        html_rendered = template.render(context)

        return mark_safe(html_rendered)
