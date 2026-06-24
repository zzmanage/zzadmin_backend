from django.contrib.auth.models import User
from django.db import models


class BaseModel(models.Model):
    """基础模型类，包含通用的审查字段"""

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by",
        verbose_name="创建人",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated_by",
        verbose_name="更新人",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_deleted_by",
        verbose_name="删除人",
    )
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    version = models.IntegerField(default=1, verbose_name="版本号")
    remark = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="备注"
    )
    
    # 多租户支持
    tenant = models.ForeignKey(
        'dashboard.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_tenant",
        verbose_name="所属租户",
        help_text="为空表示系统级数据"
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
