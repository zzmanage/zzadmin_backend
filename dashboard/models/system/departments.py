from django.db import models
from .base import BaseModel


class Department(BaseModel):
    """部门模型"""

    name = models.CharField(max_length=100, verbose_name="部门名称")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, verbose_name="上级部门"
    )
    description = models.TextField(blank=True, null=True, verbose_name="部门描述")

    key = models.CharField(
        max_length=64, unique=True, null=True, blank=True, verbose_name="关联字符"
    )
    sort = models.IntegerField(default=1, verbose_name="显示排序")
    owner = models.CharField(
        max_length=32, verbose_name="负责人", null=True, blank=True
    )
    mobile = models.CharField(
        max_length=32, verbose_name="联系电话", null=True, blank=True
    )
    email = models.EmailField(max_length=32, verbose_name="邮箱", null=True, blank=True)
    status = models.BooleanField(default=True, verbose_name="部门状态")

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门管理"
        ordering = ["id"]

    def __str__(self):
        return self.name
