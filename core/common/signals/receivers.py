from io import BytesIO
import os
from django.dispatch import receiver

from core.common.models import Resource
from core.utils import signal_util
from .signals import image_lib_add_signal, image_lib_del_signal
from django.db.models.signals import post_save, post_delete
from core.common.image_search import image_search_adapter
from django.conf import settings


# @receiver(image_lib_add_signal)
# @signal_util.safe_signal_handler
# async def staff_salary_save_signal_hendler(
#     sender, file: UploadedFile, md5: str, group: str, **kwargs
# ):
#     await image_search_adapter.image_add(file=file, md5=md5, group=group)


# @receiver(im                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   


@receiver(post_save, sender=Resource)
@signal_util.safe_signal_handler
async def res_saved(sender, instance: Resource, created, **kwargs):
    if created and instance.file_type in ["image/jpeg", "image/png"]:

        file_path = instance.file.path

        with open(file_path, "rb") as f:
            await image_search_adapter.image_add(
                file=f,
                md5=instance.md5,
                group=settings.IMAGE_SEARCH_GROUP,
                filename=os.path.basename(file_path),
                content_type=instance.file_type,
            )

@receiver(signal=post_delete, sender=Resource)
@signal_util.safe_signal_handler
def res_deleted(sender, instance: Resource, **kwargs):
    image_search_adapter.image_delete(instance.stored_name)
