from django.utils.html import format_html
from django.contrib.admin.models import LogEntry, CHANGE
from django.utils.encoding import force_str
from django.contrib.contenttypes.models import ContentType


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


def log_custom_action(request, obj, msg="执行了自定义操作", action_flag=CHANGE):
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=force_str(obj),
        action_flag=action_flag,
        change_message=msg,
    )
