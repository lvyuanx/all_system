from django.forms.widgets import ClearableFileInput
from django.utils.safestring import mark_safe

class HiddenFileInput(ClearableFileInput):

    def render(self, name, value, attrs=None, renderer=None):
        # 调用父类生成原始 input
        html = super().render(name, value, attrs, renderer)
        # 用 display:none 隐藏它
        return mark_safe(f'<div style="display:none">{html}</div>')
