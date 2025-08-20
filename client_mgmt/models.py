from django.db import models

from core.utils import model_util
from core.conf import settings

class Client(model_util.PermissionHelperMixin, models.Model):
    
    class Gender(models.TextChoices):
        MALE = 'M', "男"
        FEMALE = 'F', "女"
        UNKNOWN = 'U', "未知"
    client_name = models.CharField(max_length=255, verbose_name="客户名称")
    client_phone = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="客户电话")
    client_sex = models.CharField(max_length=1, choices=Gender.choices, default=Gender.UNKNOWN, verbose_name="性别")
    client_age = models.IntegerField(null=True, blank=True, default=None, verbose_name="客户年龄")
    company_name = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="公司名称")
    company_phone = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="公司电话")
    company_address = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="公司地址")
    company_logo = models.ImageField(upload_to=model_util.client_logo_path, blank=True, null=True, default=settings.DEFAULT_IMAGE, verbose_name="公司logo")
    is_active = models.BooleanField(default=True, null=True, verbose_name="是否激活")

    class Meta:
        verbose_name = "客户列表"
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"客户名称：{self.client_name}; 客户电话：{self.client_phone};"

