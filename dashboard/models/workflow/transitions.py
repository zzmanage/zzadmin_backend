from django.contrib.auth.models import User
from django.db import models


class WorkflowTransition(models.Model):
    """工作流流转记录模型"""
    
    task = models.ForeignKey(
        'dashboard.WorkflowTask',
        on_delete=models.CASCADE,
        related_name="transitions",
        verbose_name="关联任务"
    )
    from_state = models.CharField(max_length=50, verbose_name="原状态")
    to_state = models.CharField(max_length=50, verbose_name="目标状态")
    transition_name = models.CharField(max_length=100, verbose_name="流转名称")
    comment = models.TextField(null=True, blank=True, verbose_name="流转意见")
    data = models.JSONField(default=dict, verbose_name="流转数据")
    tenant = models.ForeignKey(
        'dashboard.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_transitions",
        verbose_name="所属租户"
    )
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_transitions",
        verbose_name="操作人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="流转时间")
    
    class Meta:
        verbose_name = "工作流流转记录"
        verbose_name_plural = "工作流流转记录管理"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Transition-{self.id} - {self.task.task_name}"
