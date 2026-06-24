"""
租户上下文管理工具
提供租户隔离和上下文管理功能
"""
import threading

# 使用 thread-local 存储租户上下文
_tenant_local = threading.local()


def set_current_tenant(tenant_id):
    """设置当前租户上下文"""
    _tenant_local.tenant_id = tenant_id


def get_current_tenant_id():
    """获取当前租户ID"""
    return getattr(_tenant_local, 'tenant_id', None)


def clear_current_tenant():
    """清除当前租户上下文"""
    if hasattr(_tenant_local, 'tenant_id'):
        del _tenant_local.tenant_id


def get_current_tenant():
    """获取当前租户对象"""
    from dashboard.models import Tenant
    tenant_id = get_current_tenant_id()
    if tenant_id:
        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return None
    return None


class TenantContext:
    """租户上下文管理器"""
    
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.previous_tenant_id = None
    
    def __enter__(self):
        self.previous_tenant_id = get_current_tenant_id()
        set_current_tenant(self.tenant_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_current_tenant(self.previous_tenant_id)
        return False
