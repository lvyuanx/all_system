from django.apps import AppConfig


class BillConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bill'
    verbose_name = '票据管理中心'
    
    
    def ready(self):
        from .signals import receivers
