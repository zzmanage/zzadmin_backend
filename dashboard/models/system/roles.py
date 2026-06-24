from django.db import models
from .base import BaseModel
from .menu_buttons import MenuButton


class Role(BaseModel):
    """角色模型"""

    name = models.CharField(max_length=100, verbose_name="角色名称")
    description = models.TextField(blank=True, null=True, verbose_name="角色描述")
    permissions = models.ManyToManyField(
        MenuButton, blank=True, verbose_name="权限"
    )

    key = models.CharField(max_length=64, unique=True, verbose_name="权限字符")
    sort = models.IntegerField(default=1, verbose_name="角色顺序")
    status = models.BooleanField(default=True, verbose_name="角色状态")
    admin = models.BooleanField(default=False, verbose_name="是否为admin")

    DATASCOPE_CHOICES = (
        (0, "仅本人数据权限"),
        (1, "本部门及以下数据权限"),
        (2, "本部门数据权限"),
        (3, "全部数据权限"),
        (4, "自定数据权限"),
    )
    data_range = models.IntegerField(
        default=0,
        choices=DATASCOPE_CHOICES,
        verbose_name="数据权限范围",
        help_text="数据权限范围",
    )

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色管理"
        ordering = ["id"]

    def __str__(self):
        return self.name
