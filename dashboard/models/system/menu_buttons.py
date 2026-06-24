from django.db import models
from .base import BaseModel


class MenuButton(BaseModel):
    """菜单按钮权限表"""

    menu = models.ForeignKey(
        to="Menu",
        db_constraint=False,
        related_name="menuPermission",
        on_delete=models.CASCADE,
        verbose_name="关联菜单",
        help_text="关联菜单",
    )
    name = models.CharField(max_length=64, verbose_name="名称", help_text="名称")
    value = models.CharField(max_length=64, verbose_name="权限值", help_text="权限值")
    api = models.CharField(max_length=64, verbose_name="接口地址", help_text="接口地址")
    METHOD_CHOICES = (
        (0, "GET"),
        (1, "POST"),
        (2, "PUT"),
        (3, "DELETE"),
    )
    method = models.SmallIntegerField(
        default=0,
        verbose_name="接口请求方法",
        null=True,
        blank=True,
        help_text="接口请求方法",
    )

    class Meta:
        verbose_name = "菜单按钮权限"
        verbose_name_plural = "菜单按钮权限"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.menu.name}-{self.name}"
