from django.dispatch import receiver

from core.common.models import Resource
from core.utils import signal_util
from .signals import image_lib_add_signal, image_lib_del_signal
from django.db.models.signals import post_save, post_delete

@receiver(image_lib_add_signal)
@signal_util.safe_signal_handler
def staff_salary_save_signal_hendler(
    sender, image_bytes: bytes, name: str, **kwargs
):
    pass
    # manager.add_images([(name, image_bytes)])


@receiver(image_lib_del_signal)
@signal_util.safe_signal_handler
def staff_salary_save_signal_hendler(
    sender, name: str, **kwargs
):
    pass
    # manager.delete_image(name)


@receiver(signal=post_save, sender=Resource)
def res_saved(sender, instance: Resource, created, **kwargs):
    if created and instance.file_type in ["image/jpeg", "image/png"]:
        pass
        # manager.add_images([(instance.stored_name, instance.file.read())], instance.category)


@receiver(signal=post_delete, sender=Resource)
def res_deleted(sender, instance: Resource, **kwargs):
    pass
    # manager.delete_image(instance.stored_name)