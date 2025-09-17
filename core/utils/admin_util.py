from django.utils.html import format_html
from django.contrib.admin.models import LogEntry, CHANGE
from django.utils.encoding import force_str
from django.contrib.contenttypes.models import ContentType
from typing import Literal


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


def format_avatar(url: str):

    return format_html(
        "<img src='{}' class='rounded-circle' width='50' height='50' />", url
    )


def log_custom_actions(
    request, objs, msg="执行了自定义操作", action_flag: Literal[1, 2, 4] = CHANGE
):
    return LogEntry.objects.log_actions(
        user_id=request.user.pk,
        queryset=objs,  # 这里必须是可迭代的
        action_flag=action_flag,
        change_message=msg,
        single_object=True,  # 保持返回单个 LogEntry
    )
