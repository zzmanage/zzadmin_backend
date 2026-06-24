from django.contrib.auth.models import User
from django.db import models


class WorkflowInstance(models.Model):
    """工作流实例模型"""
    
    STATUS_CHOICES = (
        (0, "待启动"),
        (1, "运行中"),
        (2, "已完成"),
        (3, "已终止"),
        (4, "已撤回"),
    )
    
    definition = models.ForeignKey(
        'dashboard.WorkflowDefinition',
        on_delete=models.CASCADE,
        related_name="instances",
        verbose_name="流程定义"
    )
    business_key = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="业务主键",
        help_text="关联业务数据ID"
    )
    business_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="业务类型"
    )
    status = models.IntegerField(
        default=0,
        choices=STATUS_CHOICES,
        verbose_name="状态"
    )
    data = models.JSONField(default=dict, verbose_name="流程数据")
    tenant = models.ForeignKey(
        'dashboard.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_instances",
        verbose_name="所属租户"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_instances_created",
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="启动时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    
    class Meta:
        verbose_name = "工作流实例"
        verbose_name_plural = "工作流实例管理"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Instance-{self.id} - {self.definition.name}"
