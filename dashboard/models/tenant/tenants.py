from typing import Any, Dict

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from ...utils.tenant_manager import TenantManager


class Tenant(models.Model):
    """租户模型 - 多租户架构的核心模型"""
    
    STATUS_CHOICES = (
        (0, "未激活"),
        (1, "正常"),
        (2, "暂停"),
        (3, "已删除"),
    )
    
    name = models.CharField(max_length=100, verbose_name="租户名称")
    domain = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name="租户域名",
        help_text="用于子域名访问"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="租户编码",
        help_text="唯一标识，用于数据隔离"
    )
    status = models.IntegerField(
        default=1,
        choices=STATUS_CHOICES,
        verbose_name="租户状态"
    )
    contact_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="联系人"
    )
    contact_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="联系电话"
    )
    contact_email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="联系邮箱"
    )
    max_users = models.IntegerField(
        default=100,
        verbose_name="最大用户数",
        help_text="0表示不限制"
    )
    max_storage = models.BigIntegerField(
        default=10737418240,
        verbose_name="最大存储空间(字节)",
        help_text="默认10GB"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="有效期至"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tenants',
        verbose_name="创建人"
    )
    
    objects = TenantManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = "租户"
        verbose_name_plural = "租户管理"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['code', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['domain']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.initialize_default_data()
    
    def initialize_default_data(self):
        from .tenant_settings import TenantSetting
        from .tenant_users import TenantUser
        
        TenantSetting.objects.get_or_create(
            tenant=self,
            defaults={
                'settings': {
                    'theme': 'default',
                    'language': 'zh-CN',
                    'notifications_enabled': True,
                    'timezone': 'Asia/Shanghai',
                    'date_format': 'YYYY-MM-DD',
                    'time_format': 'HH:mm:ss',
                }
            }
        )
        
        if self.created_by:
            TenantUser.objects.get_or_create(
                tenant=self,
                user=self.created_by,
                defaults={
                    'role': 'admin',
                    'is_active': True
                }
            )
    
    def get_users_count(self):
        from .tenant_users import TenantUser
        return TenantUser.objects.filter(tenant=self, is_active=True).count()
    
    def is_expired(self):
        if self.expires_at:
            return self.expires_at < timezone.now()
        return False
