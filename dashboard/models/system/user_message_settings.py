"""
用户消息接收设置模型
"""
from django.contrib.auth.models import User
from django.db import models

from .base import BaseModel


class UserMessageSettings(BaseModel):
    """用户消息接收设置模型"""
    
    # 关联用户
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="message_settings",
        verbose_name="用户"
    )
    
    # 系统通知设置
    enable_system_notify = models.BooleanField(default=True, verbose_name="启用系统通知")
    system_notify_in_app = models.BooleanField(default=True, verbose_name="系统通知-应用内")
    system_notify_email = models.BooleanField(default=False, verbose_name="系统通知-邮件")
    
    # 任务通知设置
    enable_task_notify = models.BooleanField(default=True, verbose_name="启用任务通知")
    task_notify_in_app = models.BooleanField(default=True, verbose_name="任务通知-应用内")
    task_notify_email = models.BooleanField(default=True, verbose_name="任务通知-邮件")
    
    # 告警通知设置
    enable_alert_notify = models.BooleanField(default=True, verbose_name="启用告警通知")
    alert_notify_in_app = models.BooleanField(default=True, verbose_name="告警通知-应用内")
    alert_notify_email = models.BooleanField(default=True, verbose_name="告警通知-邮件")
    alert_notify_sms = models.BooleanField(default=False, verbose_name="告警通知-短信")
    
    # 公告通知设置
    enable_announcement_notify = models.BooleanField(default=True, verbose_name="启用公告通知")
    announcement_notify_in_app = models.BooleanField(default=True, verbose_name="公告通知-应用内")
    announcement_notify_email = models.BooleanField(default=True, verbose_name="公告通知-邮件")
    
    # 通知频率设置
    email_notify_frequency = models.IntegerField(
        default=0, 
        choices=((0, "即时"), (1, "每日汇总"), (2, "每周汇总")), 
        verbose_name="邮件通知频率"
    )
    
    class Meta:
        verbose_name = "用户消息接收设置"
        verbose_name_plural = "用户消息接收设置管理"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.username}的消息接收设置"
