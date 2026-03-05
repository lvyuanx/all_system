from django.dispatch import receiver

from core.common.models import Resource
from core.utils import signal_util
from .signals import image_lib_add_signal, image_lib_del_signal
from core.common.image_search_engine import get_image_search_manager
from django.db.models.signals import post_save, post_delete

manager = get_image_search_manager()

@receiver(image_lib_add_signal)
@signal_util.safe_signal_handler
def staff_salary_save_signal_hendler(
    sender, image_bytes: bytes, name: str, **kwargs
):
    manager.add_images([(name, image_bytes)])


@receiver(image_lib_del_signal)
@signal_util.safe_signal_handler
def staff_salary_save_signal_hendler(
    sender, name: str, **kwargs
):
    manager.delete_image(name)


@receiver(signal=post_save, sender=Resource)
def res_saved(sender, instance: Resource, created, **kwargs):
    if created and instance.file_type in ["image/jpeg", "image/png"]:
        manager.add_images([(instance.stored_name, instance.file.read())], instance.category)


@receiver(signal=post_delete, sender=Resource)
def res_deleted(sender, instance: Resource, **kwargs):
    manager.delete_image(instance.stored_name)