from django.db import models
from .base import BaseModel


class Dictionary(BaseModel):
    """字典模型"""

    TYPE_LIST = (
        (0, "text"),
        (1, "number"),
        (2, "date"),
        (3, "datetime"),
        (4, "time"),
        (5, "files"),
        (6, "boolean"),
        (7, "images"),
    )
    label = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="字典名称",
        help_text="字典名称",
    )
    value = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="字典编号",
        help_text="字典编号/实际值",
    )
    parent = models.ForeignKey(
        to="self",
        related_name="sublist",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="父级",
        help_text="父级",
    )
    type = models.IntegerField(
        choices=TYPE_LIST, default=0, verbose_name="数据值类型", help_text="数据值类型"
    )
    color = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="颜色", help_text="颜色"
    )
    is_value = models.BooleanField(
        default=False,
        verbose_name="是否为value值",
        help_text="是否为value值,用来做具体值存放",
    )
    status = models.BooleanField(default=True, verbose_name="状态", help_text="状态")
    sort = models.IntegerField(
        default=1, verbose_name="显示排序", null=True, blank=True, help_text="显示排序"
    )
    remark = models.CharField(
        max_length=2000, blank=True, null=True, verbose_name="备注", help_text="备注"
    )

    class Meta:
        verbose_name = "字典"
        verbose_name_plural = "字典管理"
        ordering = ("sort",)
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'value'],
                name='unique_dictionary_value_per_parent'
            )
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.label} - {self.label}"
        return self.label
