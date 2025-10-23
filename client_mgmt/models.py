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
    address_province = models.ForeignKey(
        "core_common.ProvinceCode", on_delete=models.SET_NULL, null=True, blank=True, default=None, db_constraint=False, verbose_name="公司所在省"
    )
    address_city = models.ForeignKey(
        "core_common.CityCode", on_delete=models.SET_NULL, null=True, blank=True, default=None, db_constraint=False, verbose_name="公司所在市"
    )
    address_district = models.ForeignKey(
        "core_common.DistrictCode", on_delete=models.SET_NULL, null=True, blank=True, default=None, db_constraint=False, verbose_name="公司所在区"
    )
    address_detail = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="公司详细地址")
    company_logo = models.ImageField(upload_to=model_util.client_logo_path, blank=True, null=True, default=settings.DEFAULT_IMAGE, verbose_name="公司logo")
    is_active = models.BooleanField(default=True, null=True, verbose_name="是否激活")

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="历史下单总金额")
    total_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="欠款总额")
    total_order_count = models.IntegerField(default=0, verbose_name="历史下单总数")
    total_end_order_count = models.IntegerField(default=0, verbose_name="历史结束订单数")


    class Meta:
        verbose_name = "客户列表"
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"客户名称：{self.client_name}; 客户电话：{self.client_phone};"

