from django.db import models


class TenantSetting(models.Model):
    """租户配置模型"""
    
    tenant = models.OneToOneField(
        'dashboard.Tenant',
        on_delete=models.CASCADE,
        related_name="settings",
        verbose_name="租户"
    )
    settings = models.JSONField(default=dict, verbose_name="配置内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "租户配置"
        verbose_name_plural = "租户配置管理"
    
    def __str__(self):
        return f"{self.tenant.name} 的配置"
