# Dashboard utils package

# 租户相关工具
from .tenant_utils import (
    set_current_tenant,
    get_current_tenant_id,
    clear_current_tenant,
    get_current_tenant,
    TenantContext,
)
from .tenant_manager import TenantManager, TenantScopedManager
from .tenant_permissions import (
    tenant_permission_required,
    has_role_permission,
    get_user_tenant_role,
    is_tenant_admin,
    is_tenant_manager,
    can_access_tenant_resource,
)

__all__ = [
    # 租户上下文管理
    'set_current_tenant',
    'get_current_tenant_id',
    'clear_current_tenant',
    'get_current_tenant',
    'TenantContext',
    # 租户隔离管理器
    'TenantManager',
    'TenantScopedManager',
    # 租户权限控制
    'tenant_permission_required',
    'has_role_permission',
    'get_user_tenant_role',
    'is_tenant_admin',
    'is_tenant_manager',
    'can_access_tenant_resource',
]
