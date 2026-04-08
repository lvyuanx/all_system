import logging
import traceback

from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from core.common.models import Resource
from core.utils import signal_util
from core.utils.async_util import run_async
from core.common.image_search import image_search_adapter
from django.conf import settings
from .signals import res_unactive_signal

logger = logging.getLogger(__name__)


def _safe_run(coro, signal_name: str, context: dict):
    """执行协程，捕获异常后写入 SignalReceiverFail 并记录日志。"""
    import json
    from core.common.models import SignalReceiverFail

    try:
        run_async(coro)
    except Exception as e:
        logger.error(
            "[Signal on_commit Fail] signal=%s error=%s\n%s\ncontext=%s",
            signal_name,
            str(e),
            traceback.format_exc(),
            json.dumps(context, ensure_ascii=False, default=str),
        )
        try:
            SignalReceiverFail.objects.create(
                signal=signal_name,
                sender="core.common.models.Resource",
                context=context,
                error_message=str(e),
                traceback=traceback.format_exc(),
            )
        except Exception:
            logger.exception("[Signal on_commit Fail] 写入 SignalReceiverFail 也失败了")


@receiver(post_save, sender=Resource)
@signal_util.safe_signal_handler
def res_saved_signal_handler(sender, instance: Resource, created, **kwargs):
    if not settings.IMAGE_SEARCH_OPEN:
        return

    if created and instance.file_type in ["image/jpeg", "image/png"]:
        # 提前捕获所有需要的值，避免 on_commit 时通过 ORM 懒加载
        file_path = instance.file.path
        md5 = instance.md5
        group = settings.IMAGE_SEARCH_GROUP
        stored_name = instance.stored_name
        content_type = instance.file_type
        context = {"stored_name": stored_name, "group": group}

        # 延迟到事务提交后再调用第三方服务，避免事务回滚导致索引与数据库不一致
        def _add():
            with open(file_path, "rb") as f:
                _safe_run(
                    image_search_adapter.image_add(
                        file=f,
                        md5=md5,
                        group=group,
                        filename=stored_name,
                        content_type=content_type,
                    ),
                    signal_name="res_saved_signal_handler",
                    context=context,
                )

        transaction.on_commit(_add)


@receiver(signal=post_delete, sender=Resource)
@signal_util.safe_signal_handler
def res_deleted_signal_handler(sender, instance: Resource, **kwargs):
    if not settings.IMAGE_SEARCH_OPEN:
        return

    stored_name = instance.stored_name
    context = {"stored_name": stored_name}

    transaction.on_commit(lambda: _safe_run(
        image_search_adapter.image_delete(stored_name),
        signal_name="res_deleted_signal_handler",
        context=context,
    ))


@receiver(signal=res_unactive_signal, sender=Resource)
@signal_util.safe_signal_handler
def res_unactive_signal_handler(sender, stored_name: str, **kwargs):
    if not settings.IMAGE_SEARCH_OPEN:
        return

    context = {"stored_name": stored_name}

    transaction.on_commit(lambda: _safe_run(
        image_search_adapter.image_delete(stored_name),
        signal_name="res_unactive_signal_handler",
        context=context,
    ))
