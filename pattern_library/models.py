from django.db import models

class Pattern(models.Model):
    
    name = models.CharField(max_length=255, verbose_name="名称")
    code = models.CharField(max_length=255, verbose_name="版号")
    memo = models.CharField(max_length=255, null=True, blank=True, verbose_name="备注")
    main_image = models.OneToOneField(
        "core_common.Resource", on_delete=models.SET_NULL, null=True, blank=True, related_name="pattern_main_image", verbose_name="主图"
    )
    images = models.ManyToManyField(
        "core_common.Resource", related_name="pattern_images", verbose_name="辅图"
    )
    
    class Meta:
        verbose_name = "版式库"
        verbose_name_plural = "版式库"
