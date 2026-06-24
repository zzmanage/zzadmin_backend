from django.contrib.auth.models import User
from django.db import models


class WorkflowDefinition(models.Model):
    """工作流定义模型"""
    
    STATUS_CHOICES = (
        (0, "草稿"),
        (1, "已发布"),
        (2, "已禁用"),
    )
    
    name = models.CharField(max_length=100, verbose_name="流程名称")
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="流程编码",
        help_text="唯一标识"
    )
    description = models.TextField(null=True, blank=True, verbose_name="流程描述")
    flow_json = models.JSONField(verbose_name="流程定义JSON")
    status = models.IntegerField(
        default=1,
        choices=STATUS_CHOICES,
        verbose_name="状态"
    )
    tenant = models.ForeignKey(
        'dashboard.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_definitions",
        verbose_name="所属租户"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_definitions_created",
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "工作流定义"
        verbose_name_plural = "工作流定义管理"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
