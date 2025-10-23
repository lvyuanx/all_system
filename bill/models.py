from django.db import models
from core.utils import model_util
from core.common.generator import sn_generator

class BillTemplate(model_util.PermissionHelperMixin, models.Model):
    
    name = models.CharField(max_length=255, verbose_name="名称")
    content = models.TextField(verbose_name="内容")
    template_code = models.CharField(max_length=255, verbose_name="模板编号")
    
    class Meta:
        verbose_name = "票据模板"
        verbose_name_plural = "票据模板"
    
    def __str__(self):
        return f"{self.template_code}{self.name}"


class Bill(model_util.PermissionHelperMixin, model_util.StructureMoelMixin, models.Model):
    """
    票据
    """
    name = models.CharField(max_length=255, verbose_name="名称")
    template = models.ForeignKey(BillTemplate, on_delete=models.SET_NULL, null=True, related_name="bills", verbose_name="模板")
    params = models.JSONField(verbose_name="参数", null=True, blank=True)
    bill_path = models.CharField(max_length=255, null=True, verbose_name="票据路径")
    sn = models.CharField(max_length=255, null=True, verbose_name="票据编号")
    
    @staticmethod
    def get_sn(count=1):
        return sn_generator.next_ids(
            count, prefix="B", used_for="bill.Bill", letter_length=0
        )

    def save(self, *args, **kwargs):
        if not self.sn:  # 只有保存时才生成
            self.sn = self.get_sn()[0]
        super().save(*args, **kwargs)


    class Meta:
        verbose_name = "票据库"
        verbose_name_plural = verbose_name
    
    def __str__(self) -> str:
        return f"{self.name}"

