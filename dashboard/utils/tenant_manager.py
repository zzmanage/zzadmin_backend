"""
租户隔离的 Model Manager
自动根据当前租户上下文过滤数据
"""
from django.db import models

from dashboard.utils.tenant_utils import get_current_tenant_id


class TenantManager(models.Manager):
    """
    租户隔离的模型管理器
    
    自动根据当前租户上下文过滤数据，确保数据隔离。
    使用方法：
    class MyModel(models.Model):
        tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
        # ... 其他字段
        
        objects = TenantManager()
    
    注意：使用此 Manager 的模型必须有 tenant 字段
    """
    
    def get_queryset(self):
        """获取查询集，自动过滤当前租户数据"""
        queryset = super().get_queryset()
        tenant_id = get_current_tenant_id()
        
        if tenant_id:
            # 如果有租户上下文，过滤该租户的数据
            return queryset.filter(tenant_id=tenant_id)
        
        # 如果没有租户上下文（如超级管理员），返回所有数据
        return queryset
    
    def for_tenant(self, tenant_id):
        """获取指定租户的数据"""
        return super().get_queryset().filter(tenant_id=tenant_id)
    
    def system_data(self):
        """获取系统级数据（tenant 为空的数据）"""
        return super().get_queryset().filter(tenant__isnull=True)


class TenantScopedManager(TenantManager):
    """
    租户作用域管理器（增强版）
    
    支持全局查询和租户查询模式切换
    """
    
    def __init__(self, allow_global=False):
        super().__init__()
        self.allow_global = allow_global
    
    def get_queryset(self):
        queryset = super(TenantManager, self).get_queryset()
        tenant_id = get_current_tenant_id()
        
        if tenant_id:
            return queryset.filter(tenant_id=tenant_id)
        elif not self.allow_global:
            # 如果不允许全局查询且没有租户上下文，返回空查询集
            return queryset.none()
        
        return queryset
    
    def all_global(self):
        """获取所有数据（忽略租户上下文）"""
        return super(TenantManager, self).get_queryset()
