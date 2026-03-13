import functools
import logging
import traceback
from django.forms.models import model_to_dict
from core.common.models import SignalReceiverFail
from core.utils.orjson_util import json

logger = logging.getLogger(__name__)

import functools
import inspect
import json
import traceback

from django.forms.models import model_to_dict

def safe_signal_handler(func):
    """
    支持同步 / 异步 signal handler
    自动记录异常日志和数据库
    """

    signal_name = func.__name__

    def build_context(args, kwargs):
        return {
            "args": [
                model_to_dict(a) if hasattr(a, "_meta") else a
                for a in args
            ],
            "kwargs": {
                k: (model_to_dict(v) if hasattr(v, "_meta") else v)
                for k, v in kwargs.items()
            },
        }

    def get_sender(sender):
        if sender:
            return f"{sender.__module__}.{getattr(sender, '__name__', str(sender))}"
        return None

    # ---------- async handler ----------
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(sender, *args, **kwargs):
            try:
                return await func(sender, *args, **kwargs)

            except Exception as e:
                context = build_context(args, kwargs)

                logger.error(
                    "[Signal Fail] signal=%s sender=%s error=%s\n%s\ncontext=%s",
                    signal_name,
                    getattr(sender, "__name__", str(sender)),
                    str(e),
                    traceback.format_exc(),
                    json.dumps(context, ensure_ascii=False, default=str),
                )

                SignalReceiverFail.objects.create(
                    signal=signal_name,
                    sender=get_sender(sender),
                    context=context,
                    error_message=str(e),
                    traceback=traceback.format_exc(),
                )

                raise

        return async_wrapper

    # ---------- sync handler ----------
    else:

        @functools.wraps(func)
        def sync_wrapper(sender, *args, **kwargs):
            try:
                return func(sender, *args, **kwargs)

            except Exception as e:
                context = build_context(args, kwargs)

                logger.error(
                    "[Signal Fail] signal=%s sender=%s error=%s\n%s\ncontext=%s",
                    signal_name,
                    getattr(sender, "__name__", str(sender)),
                    str(e),
                    traceback.format_exc(),
                    json.dumps(context, ensure_ascii=False, default=str),
                )

                SignalReceiverFail.objects.create(
                    signal=signal_name,
                    sender=get_sender(sender),
                    context=context,
                    error_message=str(e),
                    traceback=traceback.format_exc(),
                )

                raise

        return sync_wrapper