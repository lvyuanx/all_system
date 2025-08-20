from django.apps import AppConfig


class CoreNinjaExtraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.ninja_extra' 
    label = 'core_ninja_extra'
    verbose_name = "Ninja扩展"
