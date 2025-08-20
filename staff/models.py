from django.db import models
from core.utils import model_util

# Create your models here.
class Staff(model_util.PermissionHelperMixin, models.Model):
    
    user = models.OneToOneField("core_auth.User", on_delete=models.CASCADE, related_name="staff", verbose_name="用户")
    staff_code = models.CharField(max_length=50, verbose_name="员工编号")

    
    class Meta:
        verbose_name = "员工列表"
        verbose_name_plural = verbose_name
        
