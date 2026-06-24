from django.db import models
from .base import BaseModel


class TaskLog(BaseModel):
    """定时任务日志模型"""

    STATUS_FAILED = 0
    STATUS_SUCCESS = 1
    STATUS_RUNNING = 2
    STATUS_REVOKED = 3
    STATUS_RETRY = 4

    STATUS_CHOICES = (
        (STATUS_FAILED, "失败"),
        (STATUS_SUCCESS, "成功"),
        (STATUS_RUNNING, "运行中"),
        (STATUS_REVOKED, "已撤销"),
        (STATUS_RETRY, "重试中"),
    )

    periodic_task = models.ForeignKey(
        "django_celery_beat.PeriodicTask",
        on_delete=models.CASCADE,
        verbose_name="定时任务",
        null=True,
        blank=True,
    )

    task_name = models.CharField(max_length=255, verbose_name="任务名称")
    task_id = models.CharField(
        max_length=100, verbose_name="任务ID", unique=True, null=True, blank=True
    )

    status = models.IntegerField(
        choices=STATUS_CHOICES, default=2, verbose_name="执行状态"
    )
    result = models.TextField(verbose_name="执行结果", null=True, blank=True)
    error_message = models.TextField(verbose_name="错误信息", null=True, blank=True)

    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间", null=True, blank=True)
    duration = models.FloatField(verbose_name="执行时长(秒)", null=True, blank=True)

    args = models.TextField(verbose_name="任务参数", null=True, blank=True)
    kwargs = models.TextField(verbose_name="关键字参数", null=True, blank=True)
    retry_count = models.IntegerField(default=0, verbose_name="重试次数")
    progress = models.IntegerField(default=0, verbose_name="任务进度(%)", help_text="0-100之间的整数")

    class Meta:
        verbose_name = "定时任务日志"
        verbose_name_plural = "定时任务日志管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_name} - {self.get_status_display()} - {self.start_time}"
