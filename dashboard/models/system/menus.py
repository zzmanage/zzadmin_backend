from django.db import models
from .base import BaseModel


class Menu(BaseModel):
    """菜单模型"""

    parent = models.ForeignKey(
        to="Menu",
        on_delete=models.CASCADE,
        verbose_name="上级菜单",
        null=True,
        blank=True,
        help_text="上级菜单",
    )
    icon = models.CharField(
        max_length=64,
        verbose_name="菜单图标",
        null=True,
        blank=True,
        help_text="菜单图标",
    )
    name = models.CharField(
        max_length=64, verbose_name="菜单名称", help_text="菜单名称"
    )
    sort = models.IntegerField(
        default=1, verbose_name="显示排序", null=True, blank=True, help_text="显示排序"
    )
    is_link = models.BooleanField(
        default=False, verbose_name="是否外链", help_text="是否外链"
    )
    is_catalog = models.BooleanField(
        default=False, verbose_name="是否目录", help_text="是否目录"
    )
    web_path = models.CharField(
        max_length=128,
        verbose_name="路由地址",
        null=True,
        blank=True,
        help_text="路由地址",
    )
    component = models.CharField(
        max_length=128,
        verbose_name="组件地址",
        null=True,
        blank=True,
        help_text="组件地址",
    )
    component_name = models.CharField(
        max_length=50,
        verbose_name="组件名称",
        null=True,
        blank=True,
        help_text="组件名称",
    )
    status = models.BooleanField(
        default=True, blank=True, verbose_name="菜单状态", help_text="菜单状态"
    )
    cache = models.BooleanField(
        default=False, blank=True, verbose_name="是否页面缓存", help_text="是否页面缓存"
    )
    visible = models.BooleanField(
        default=True,
        blank=True,
        verbose_name="侧边栏中是否显示",
        help_text="侧边栏中是否显示",
    )

    class Meta:
        verbose_name = "菜单"
        verbose_name_plural = "菜单管理"
        ordering = ("sort",)

    def __str__(self):
        return self.name
