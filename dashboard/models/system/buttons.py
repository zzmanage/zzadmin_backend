from django.db import models
from .base import BaseModel


class Button(BaseModel):
    """按钮模型"""

    name = models.CharField(
        max_length=64, verbose_name="按钮名称", help_text="按钮名称"
    )
    value = models.CharField(
        max_length=64, verbose_name="按钮值", help_text="按钮值", unique=True
    )

    class Meta:
        verbose_name = "按钮"
        verbose_name_plural = "按钮管理"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
