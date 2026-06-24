from django.db import models
from .base import BaseModel


class ApiWhiteList(BaseModel):
    """接口白名单模型"""

    url = models.CharField(max_length=200, help_text="url地址", verbose_name="url")
    METHOD_CHOICES = (
        (0, "GET"),
        (1, "POST"),
        (2, "PUT"),
        (3, "DELETE"),
    )
    method = models.IntegerField(
        default=0,
        verbose_name="接口请求方法",
        null=True,
        blank=True,
        help_text="接口请求方法",
    )
    enable_datasource = models.BooleanField(
        default=True, verbose_name="激活数据权限", help_text="激活数据权限", blank=True
    )

    class Meta:
        verbose_name = "接口白名单"
        verbose_name_plural = "接口白名单管理"
        ordering = ("-created_at",)
        unique_together = ("url", "method")

    def __str__(self):
        method_display = dict(self.METHOD_CHOICES).get(self.method, "ALL")
        return f"{method_display} {self.url}"
