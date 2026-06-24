"""
操作日志模型
"""
from django.contrib.auth.models import User
from django.db import models

from .base import BaseModel


class OperationLog(BaseModel):
    """操作日志模型"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="操作用户")
    operation = models.CharField(max_length=200, verbose_name="操作内容")
    module = models.CharField(max_length=100, verbose_name="操作模块")
    ip_address = models.CharField(max_length=50, verbose_name="IP地址")

    # 添加的字段
    action = models.CharField(
        max_length=50, verbose_name="操作类型", null=True, blank=True
    )
    model_name = models.CharField(
        max_length=100, verbose_name="模型名称", null=True, blank=True
    )
    model_id = models.IntegerField(verbose_name="模型ID", null=True, blank=True)
    details = models.TextField(verbose_name="操作详情", null=True, blank=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.operation} - {self.created_at}"
