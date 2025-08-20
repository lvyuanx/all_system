from django.apps import AppConfig


class CoreAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.system' 
    label = 'core_system'
    verbose_name = "系统管理"
    
    
    # def ready(self):
    #     from . import signals
