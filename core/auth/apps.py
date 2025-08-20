from django.apps import AppConfig


class CoreAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.auth' 
    label = 'core_auth'  # 避免与内置 auth 冲突
    verbose_name = "用户管理"
    
    
    def ready(self):
        from . import signals
