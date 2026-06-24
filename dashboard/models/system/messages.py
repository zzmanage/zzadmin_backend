from django.contrib.auth.models import User
from django.db import models
from .base import BaseModel


class Message(BaseModel):
    """消息元数据模型"""

    title = models.CharField(max_length=200, verbose_name="消息标题")
    content = models.TextField(verbose_name="消息内容")
    sender = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="发送者"
    )

    RECEIVE_TYPE_CHOICES = (
        (0, "全部"),
        (1, "部门"),
        (2, "角色"),
        (3, "指定用户"),
    )
    receive_type = models.IntegerField(
        choices=RECEIVE_TYPE_CHOICES, verbose_name="接收类型"
    )
    receive_target = models.IntegerField(
        null=True, blank=True, verbose_name="接收目标ID"
    )

    MESSAGE_TYPE_CHOICES = (
        ("system", "系统通知"),
        ("task", "任务通知"),
        ("alert", "告警通知"),
        ("announcement", "公告"),
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default="system",
        verbose_name="消息类型",
    )

    PRIORITY_CHOICES = (
        (0, "普通"),
        (1, "重要"),
        (2, "紧急"),
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES, default=0, verbose_name="优先级"
    )
    
    expire_time = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    
    STATUS_CHOICES = (
        (0, "草稿"),
        (1, "已发布"),
        (2, "已撤回"),
        (3, "已过期"),
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=1, verbose_name="消息状态"
    )

    class Meta:
        verbose_name = "消息元数据"
        verbose_name_plural = "消息元数据管理"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class UserMessage(BaseModel):
    """用户消息记录模型"""

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="user_messages",
        verbose_name="消息元数据",
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_messages",
        verbose_name="接收用户",
    )

    is_read = models.BooleanField(default=False, verbose_name="是否已读")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="阅读时间")
    is_processed = models.BooleanField(default=False, verbose_name="是否已处理")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="处理时间")

    class Meta:
        verbose_name = "用户消息记录"
        verbose_name_plural = "用户消息记录管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.message.title} - {self.recipient.username}"


class UserMessageSettings(BaseModel):
    """用户消息接收设置模型"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="message_settings",
        verbose_name="用户"
    )
    
    enable_system_notify = models.BooleanField(default=True, verbose_name="启用系统通知")
    system_notify_in_app = models.BooleanField(default=True, verbose_name="系统通知-应用内")
    system_notify_email = models.BooleanField(default=False, verbose_name="系统通知-邮件")
    
    enable_task_notify = models.BooleanField(default=True, verbose_name="启用任务通知")
    task_notify_in_app = models.BooleanField(default=True, verbose_name="任务通知-应用内")
    task_notify_email = models.BooleanField(default=True, verbose_name="任务通知-邮件")
    
    enable_alert_notify = models.BooleanField(default=True, verbose_name="启用告警通知")
    alert_notify_in_app = models.BooleanField(default=True, verbose_name="告警通知-应用内")
    alert_notify_email = models.BooleanField(default=True, verbose_name="告警通知-邮件")
    alert_notify_sms = models.BooleanField(default=False, verbose_name="告警通知-短信")
    
    enable_announcement_notify = models.BooleanField(default=True, verbose_name="启用公告通知")
    announcement_notify_in_app = models.BooleanField(default=True, verbose_name="公告通知-应用内")
    announcement_notify_email = models.BooleanField(default=True, verbose_name="公告通知-邮件")
    
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
