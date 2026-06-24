from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class TenantUser(models.Model):
    """租户用户关联模型"""
    
    ROLE_CHOICES = (
        ("admin", "租户管理员"),
        ("manager", "租户经理"),
        ("user", "普通用户"),
    )
    
    tenant = models.ForeignKey(
        'dashboard.Tenant',
        on_delete=models.CASCADE,
        related_name="tenant_users",
        verbose_name="租户"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_tenants",
        verbose_name="用户"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user",
        verbose_name="租户角色"
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="加入时间")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    last_access_at = models.DateTimeField(null=True, blank=True, verbose_name="最后访问时间")
    
    class Meta:
        verbose_name = "租户用户"
        verbose_name_plural = "租户用户管理"
        unique_together = ("tenant", "user")
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['tenant', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.username} @ {self.tenant.name}"
    
    def update_last_access(self):
        self.last_access_at = timezone.now()
        self.save(update_fields=['last_access_at'])
