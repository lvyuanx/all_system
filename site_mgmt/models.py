from django.db import models

from core.conf import settings
from core.utils import model_util 

class SysSite(models.Model):
    
    site_name = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="站点名称")
    site_logo = models.ImageField(upload_to=model_util.site_logo_path, blank=True, null=True, default=settings.DEFAULT_IMAGE, verbose_name="站点logo")

    class Meta:
        verbose_name = "系统站点"
        verbose_name_plural = "系统站点"
    
    
    def __str__(self) -> str:
        return self.site_name
    


class SiteAddress(models.Model):
    
    site = models.ForeignKey(
        "SysSite", on_delete=models.SET_NULL, null=True, blank=True, default=None, db_constraint=False, verbose_name="站点"
    )
    
    address_province = models.ForeignKey(
        "core_common.ProvinceCode", on_delete=models.SET_NULL, null=True, blank=True, default=None, db_constraint=False, verbose_name="站点所在省"
    )
    address_city = models.ForeignKey(
        "core_common.CityCode", on_delete=models.SET_NULL, null=True, blank=True, default=None, db_constraint=False, verbose_name="站点所在市"
    )
    address_district = models.ForeignKey(
        "core_common.DistrictCode", on_delete=models.SET_NULL, null=True, blank=True, default=None, db_constraint=False, verbose_name="站点所在区"
    )
    address_detail = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="站点详细地址")
    site_person_in_charge = models.ForeignKey(
        "core_auth.User", on_delete=models.SET_NULL, null=True, blank=True, default=None, db_constraint=False, verbose_name="站点负责人"
    )
    contact_number = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="联系电话")
    
    
    class Meta:
        verbose_name = "站点地址"
        verbose_name_plural = "站点地址"
        
    
    def __str__(self) -> str:
        return (
            (str(self.address_province or ""))
            + (str(self.address_city or ""))
            + (str(self.address_district or ""))
            + (str(self.address_detail or ""))
        )