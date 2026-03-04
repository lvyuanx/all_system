from django.db import models

from core.utils import model_util

class Pattern(model_util.PermissionHelperMixin, model_util.StructureMoelMixin, models.Model):
    
    code = models.CharField(max_length=255, unique=True, verbose_name="版号")
    memo = models.CharField(max_length=255, null=True, blank=True, verbose_name="备注")
    main_image = models.OneToOneField(
        "core_common.Resource", on_delete=models.SET_NULL, null=True, blank=True, related_name="pattern_main_image", verbose_name="主图"
    )
    images = models.ManyToManyField(
        "core_common.Resource", related_name="pattern_images", verbose_name="辅图"
    )
    tags = models.CharField(max_length=255, default="", verbose_name="标签")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    
    
    class Meta:
        verbose_name = "版式库"
        verbose_name_plural = "版式库"
    
    
    @staticmethod
    def generate_tags( *tags: str) -> str:
        if not tags: return
        return "," + ",".join(tags) + ","
    
    @property
    def tags_lst(self):
        return [item for item in self.tags.split(",") if item]
        
    def get_add_tags_result(self, *tags: str):
        old_tags = [item for item in self.tags.split(",") if item]
        merged_tags = list(set(old_tags + list(tags)))
        return self.__class__.generate_tags(*merged_tags)
    
    def get_del_tags_result(self, *tags: str):
        old_tags = [item for item in self.tags.split(",") if item]
        del_tags = list(set(old_tags) - set(tags))
        return self.__class__.generate_tags(del_tags)

        

