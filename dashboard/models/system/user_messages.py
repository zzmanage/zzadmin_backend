"""
用户消息记录模型
"""
from django.contrib.auth.models import User
from django.db import models

from .base import BaseModel
from .messages import Message


class UserMessage(BaseModel):
    """用户消息记录模型"""

    # 关联消息元数据和接收用户
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

    # 消息状态
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
