from django.db import models
from .base import BaseModel


class Permission(BaseModel):
    """权限模型"""

    name = models.CharField(max_length=100, verbose_name="权限名称")
    code = models.CharField(max_length=100, unique=True, verbose_name="权限编码")
    description = models.TextField(blank=True, null=True, verbose_name="权限描述")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, verbose_name="上级权限"
    )

    class Meta:
        verbose_name = "权限"
        verbose_name_plural = "权限管理"
        ordering = ["id"]

    def __str__(self):
        return self.name
