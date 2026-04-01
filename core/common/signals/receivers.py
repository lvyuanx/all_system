from io import BytesIO
import os
from django.dispatch import receiver

from core.common.models import Resource
from core.utils import signal_util
from django.db.models.signals import post_save, post_delete
from core.common.image_search import image_search_adapter
from django.conf import settings
from .signals import res_unactive_signal


@receiver(post_save, sender=Resource)
@signal_util.safe_signal_handler
async def res_saved_signal_handler(sender, instance: Resource, created, **kwargs):

    if not settings.IMAGE_SEARCH_OPEN:
        return
    
    if created and instance.file_type in ["image/jpeg", "image/png"]:

        file_path = instance.file.path

        with open(file_path, "rb") as f:
            await image_search_adapter.image_add(
                file=f,
                md5=instance.md5,
                group=settings.IMAGE_SEARCH_GROUP,
                filename=instance.stored_name,
                content_type=instance.file_type,
            )

@receiver(signal=post_delete, sender=Resource)
@signal_util.safe_signal_handler
def res_deleted_signal_handler(sender, instance: Resource, **kwargs):
    if not settings.IMAGE_SEARCH_OPEN:
        return
    image_search_adapter.image_delete(instance.stored_name)



@receiver(signal=res_unactive_signal, sender=Resource)
@signal_util.safe_signal_handler
def res_unactive_signal_handler(sender, stored_name: str, **kwargs):
    if not settings.IMAGE_SEARCH_OPEN:
        return
    image_search_adapter.image_delete(stored_name)
