import functools
import logging
import traceback
import json
from django.forms.models import model_to_dict
from core.common.models import SignalReceiverFail

logger = logging.getLogger(__name__)

def safe_signal_handler(func):
    """
    包装信号处理函数，自动捕获异常并落表。
    记录 sender、args、kwargs、traceback 到日志和数据库。
    如果 sender 是 Django 模型实例，会先转成 dict。
    """
    signal_name = func.__name__

    @functools.wraps(func)
    def wrapper(sender, *args, **kwargs):
        try:
            return func(sender, *args, **kwargs)
        except Exception as e:
            # 准备上下文数据
            context = {
                "args": [
                    model_to_dict(a) if hasattr(a, "_meta") else a
                    for a in args
                ],
                "kwargs": {
                    k: (model_to_dict(v) if hasattr(v, "_meta") else v)
                    for k, v in kwargs.items()
                },
            }

            # 日志输出 JSON 字符串
            logger.error(
                "[Signal Fail] signal=%s sender=%s error=%s\n%s\ncontext=%s",
                signal_name,
                getattr(sender, "__name__", str(sender)),
                str(e),
                traceback.format_exc(),
                json.dumps(context, ensure_ascii=False, default=str)
            )

            # 落表，JSONField 可以直接存 dict
            SignalReceiverFail.objects.create(
                signal=signal_name,
                sender=f"{sender.__module__}.{sender.__name__}" if sender else None,
                context=context,
                error_message=str(e),
                traceback=traceback.format_exc(),
            )

            raise
    return wrapper
