import os
import uuid
from core.common.utils.upload_util import resource_upload_to
from core.utils.orjson_util import json
from django.db import models
import mimetypes
import hashlib

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.utils import common_util

User = get_user_model()


class SerialNumber(models.Model):
    """存储已生成的流水号，用数据库唯一约束保证全局唯一"""

    sn = models.CharField("流水号", max_length=64, unique=True, db_index=True)
    used_for = models.CharField("使用表/用途", max_length=64, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "serial_number"
        verbose_name = "流水号"
        verbose_name_plural = "流水号"
    
    def __str__(self):
        return f"{self.used_for}:{self.sn}"


class SignalReceiverFail(models.Model):
    # 信号来源
    signal = models.CharField(max_length=255, help_text="信号名称，例如 after_created_expense_salary_signal")
    sender = models.CharField(max_length=255, blank=True, null=True, help_text="发送者类路径（如果有）")

    # 通用上下文数据
    context = models.JSONField(blank=True, null=True, help_text="信号参数上下文，存储所有 args/kwargs")

    # 错误信息
    error_message = models.TextField(help_text="错误信息")
    traceback = models.TextField(blank=True, null=True, help_text="完整 traceback")

    # 状态管理
    is_recovered = models.BooleanField(default=False, help_text="是否已恢复处理")
    created_at = models.DateTimeField(auto_now_add=True)
    recovered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.signal} from {self.sender or 'unknown'}"

    def to_json(self):
        """方便调试用"""
        return json.dumps({
            "signal": self.signal,
            "sender": self.sender,
            "context": self.context,
            "error_message": self.error_message,
            "is_recovered": self.is_recovered,
        }, ensure_ascii=False, indent=2)


class ProvinceCode(models.Model):
    """省份代码"""
    code = models.CharField("代码", max_length=64, unique=True)
    name = models.CharField("名称", max_length=64)
    
    class Meta:
        verbose_name = "省份代码"
        verbose_name_plural = "省份代码"
        ordering = ["code"]
    
    def __str__(self):
        return self.name
    
class CityCode(models.Model):
    """城市代码"""
    code = models.CharField("代码", max_length=64, unique=True)
    name = models.CharField("名称", max_length=64)
    province = models.ForeignKey(ProvinceCode, on_delete=models.CASCADE, related_name="cities", db_constraint=False)
    
    class Meta:
        verbose_name = "城市代码"
        verbose_name_plural = "城市代码"
        ordering = ["code"]
    
    def __str__(self):
        return self.name

class DistrictCode(models.Model):
    """区县代码"""
    code = models.CharField("代码", max_length=64, unique=True)
    name = models.CharField("名称", max_length=64)
    city = models.ForeignKey(CityCode, on_delete=models.CASCADE, related_name="districts", db_constraint=False)
    
    class Meta:
        verbose_name = "区县代码"
        verbose_name_plural = "区县代码"
        ordering = ["code"]
    
    def __str__(self):
        return self.name


class Resource(models.Model):
    """
    通用资源表，用于存储各类文件（图片、CAD、PDF、视频等）。
    可关联任意模型（通用外键）。
    """
    name = models.CharField(max_length=255, help_text="原始文件名称")
    stored_name = models.CharField(max_length=255, blank=True, null=True, help_text="实际保存文件名")
    file = models.FileField(upload_to=resource_upload_to, help_text="文件路径")
    file_type = models.CharField(max_length=50, blank=True, null=True, help_text="MIME类型")
    size = models.BigIntegerField(blank=True, null=True, help_text="文件大小（字节）")
    md5 = models.CharField(max_length=32, blank=True, null=True, help_text="文件MD5，用于去重")
    category = models.CharField(max_length=100, blank=True, null=True, help_text="资源分类")

    # 通用外键关联
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "common_resource"
        verbose_name = "通用资源"
        verbose_name_plural = "通用资源"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or str(self.file)

    def save(self, *args, **kwargs):
        """
        保存时自动：
        - 保存原始文件名；
        - 记录实际保存的文件名；
        - 计算大小、MIME类型、MD5。
        """
        if self.file:
            # 1️⃣ 实际保存文件名
            stored_filename = os.path.basename(self.file.name)
            if not self.stored_name:
                self.stored_name = stored_filename
                
            # 2️⃣ 修改文件保存名称
            if not self.name:
                ext = os.path.splitext(stored_filename)[1]
                self.name = f"{uuid.uuid4().hex}{ext}"

            # 3️⃣ 文件大小
            if not self.size:
                self.size = self.file.size

            # 4️⃣ MIME 类型
            if not self.file_type:
                mime, _ = mimetypes.guess_type(self.file.name)
                self.file_type = mime

            # 5️⃣ MD5 校验
            if not self.md5:
                md5_hash = hashlib.md5()
                for chunk in self.file.chunks():
                    md5_hash.update(chunk)
                self.md5 = md5_hash.hexdigest()

        super().save(*args, **kwargs)
