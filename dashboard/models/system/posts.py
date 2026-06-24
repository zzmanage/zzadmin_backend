from django.db import models
from .base import BaseModel


class Post(BaseModel):
    """岗位模型"""

    name = models.CharField(
        null=False, max_length=64, verbose_name="岗位名称", help_text="岗位名称"
    )
    code = models.CharField(
        max_length=32, verbose_name="岗位编码", help_text="岗位编码"
    )
    sort = models.IntegerField(default=1, verbose_name="岗位顺序", help_text="岗位顺序")
    STATUS_CHOICES = (
        (0, "停用"),
        (1, "正常"),
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=1, verbose_name="岗位状态", help_text="岗位状态"
    )

    class Meta:
        verbose_name = "岗位"
        verbose_name_plural = "岗位管理"
        ordering = ("sort",)

    def __str__(self):
        return self.name
