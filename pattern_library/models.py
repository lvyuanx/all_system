from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from core.utils import model_util


class PatternCategory(
    model_util.PermissionHelperMixin, model_util.StructureMoelMixin, models.Model
):
    class DateMode(models.TextChoices):
        NONE = "none", "无日期"
        YEAR = "year", "年"
        MONTH = "month", "年月"
        DAY = "day", "年月日"

    name = models.CharField(max_length=100, unique=True, verbose_name="类别名称")
    code_prefix = models.CharField(max_length=32, verbose_name="版号前缀")
    date_mode = models.CharField(
        max_length=16,
        choices=DateMode.choices,
        default=DateMode.DAY,
        verbose_name="日期规则",
    )
    serial_digits = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        verbose_name="流水号位数",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        verbose_name = "版式类别"
        verbose_name_plural = "版式类别"

    def __str__(self):
        return self.name


class PatternCategorySerial(models.Model):
    category = models.ForeignKey(
        PatternCategory,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="serials",
        verbose_name="类别",
    )
    date_key = models.CharField(max_length=16, default="", verbose_name="日期键")
    current_serial = models.PositiveIntegerField(default=0, verbose_name="当前序号")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "版式类别流水"
        verbose_name_plural = "版式类别流水"
        constraints = [
            models.UniqueConstraint(
                fields=["category", "date_key"], name="uniq_pattern_category_date_key"
            )
        ]

    def __str__(self):
        return f"{self.category_id}:{self.date_key}:{self.current_serial}"


class Pattern(model_util.PermissionHelperMixin, model_util.StructureMoelMixin, models.Model):
    
    code = models.CharField(max_length=255, unique=True, verbose_name="版号")
    category = models.ForeignKey(
        PatternCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_constraint=False,
        related_name="patterns",
        verbose_name="类别",
    )
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
        if not tags:
            return ""
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

        

