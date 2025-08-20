from django.db import models
from django.contrib.auth import get_user_model
from core.utils import time_util, model_util

class BillTemplate(model_util.PermissionHelperMixin, models.Model):
    
    name = models.CharField(max_length=255, verbose_name="名称")
    content = models.TextField(verbose_name="内容")
    
    class Meta:
        verbose_name = "票据模板"
        verbose_name_plural = "票据模板"
    
    def __str__(self):
        return self.name


class Bill(model_util.PermissionHelperMixin, model_util.StructureMoelMixin, models.Model):
    """
    票据
    """
    name = models.CharField(max_length=255, verbose_name="名称")
    template = models.ForeignKey(BillTemplate, on_delete=models.SET_NULL, null=True, related_name="bills", verbose_name="模板")
    params = models.JSONField(verbose_name="参数", null=True, blank=True)
    bill_path = models.CharField(max_length=255, null=True, verbose_name="票据路径")


    class Meta:
        verbose_name = "票据库"
        verbose_name_plural = verbose_name
    
    def __str__(self) -> str:
        return self.name

