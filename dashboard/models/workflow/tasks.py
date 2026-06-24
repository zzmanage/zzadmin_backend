from django.contrib.auth.models import User
from django.db import models


class WorkflowTask(models.Model):
    """工作流任务节点模型"""
    
    STATUS_CHOICES = (
        (0, "待处理"),
        (1, "处理中"),
        (2, "已完成"),
        (3, "已拒绝"),
        (4, "已跳过"),
    )
    
    instance = models.ForeignKey(
        'dashboard.WorkflowInstance',
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="流程实例"
    )
    task_def_key = models.CharField(max_length=100, verbose_name="任务定义Key")
    task_name = models.CharField(max_length=100, verbose_name="任务名称")
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_tasks_assigned",
        verbose_name="处理人"
    )
    candidate_users = models.JSONField(
        default=list,
        verbose_name="候选用户列表",
        help_text="用户ID列表"
    )
    candidate_roles = models.JSONField(
        default=list,
        verbose_name="候选角色列表",
        help_text="角色ID列表"
    )
    status = models.IntegerField(
        default=0,
        choices=STATUS_CHOICES,
        verbose_name="状态"
    )
    comment = models.TextField(null=True, blank=True, verbose_name="处理意见")
    data = models.JSONField(default=dict, verbose_name="任务数据")
    tenant = models.ForeignKey(
        'dashboard.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_tasks",
        verbose_name="所属租户"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始处理时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    
    class Meta:
        verbose_name = "工作流任务"
        verbose_name_plural = "工作流任务管理"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Task-{self.id} - {self.task_name}"
