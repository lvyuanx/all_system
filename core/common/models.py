from core.utils.orjson_util import json
from django.db import models


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
