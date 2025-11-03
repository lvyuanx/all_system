import inspect
import os
from django import forms
from django.template import Context, Engine
from django.utils.safestring import mark_safe


class BaseWidget(forms.Widget):
    """自定义组件基类"""

    html_name = None

    def __init__(self, attrs=None):
        super().__init__(attrs)
        # 读取 html 模板
        subclass_file = inspect.getfile(self.__class__)
        current_dir = os.path.dirname(os.path.abspath(subclass_file))
        html_path = os.path.join(current_dir, self.html_name)
        with open(html_path, "r", encoding="utf-8") as f:
            self.widget_html = f.read()

    def render(self, name, value, attrs=None, renderer=None):
        """
        name: 当前字段名（这里是 linkage）
        attrs: 可以由外部传入的初始值
        """
        origin_attrs = self.attrs.get("origin_attrs")
        if not origin_attrs:
            raise ValueError("请传入 origin_attrs 参数")
        
        hiden_inputs = []
        
        for origin_attr in origin_attrs:
            oa_value = self.attrs.get(origin_attr, "")
            hiden_inputs.append(
                f'<input type="hidden" name="custom_widget_{origin_attr}" value="{oa_value}">'
            )
        hiden_input_str = "\n".join(hiden_inputs)
        html = f"""
        {hiden_input_str}
        {self.widget_html}
        """
    
        # 用 Django 模板引擎渲染 HTML
        engine = Engine(debug=False)
        template = engine.from_string(html)
        context = Context(self.attrs.get("context", {}))
        html_rendered = template.render(context)

        return mark_safe(html_rendered)
