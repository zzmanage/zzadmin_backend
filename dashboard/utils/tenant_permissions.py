"""
租户权限控制工具
提供租户级别的权限验证和装饰器
"""
from functools import wraps
from typing import Callable, Optional

from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response

from dashboard.utils.tenant_utils import get_current_tenant_id


def tenant_permission_required(permission_code: str):
    """
    租户权限装饰器
    
    用于验证用户是否具有指定的租户权限
    
    使用方法：
    @tenant_permission_required('tenant.user.view')
    def my_view(request):
        # 视图逻辑
        pass
    """
    def decorator(view_func: Callable):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            from dashboard.models import TenantUser
            
            tenant_id = get_current_tenant_id()
            
            if not tenant_id:
                # 如果没有租户上下文，允许访问（可能是系统管理员）
                return view_func(request, *args, **kwargs)
            
            # 检查用户是否在租户中具有相应权限
            user = request.user
            
            try:
                tenant_user = TenantUser.objects.get(tenant_id=tenant_id, user=user)
                
                # 根据角色判断权限
                if has_role_permission(tenant_user.role, permission_code):
                    return view_func(request, *args, **kwargs)
                
                return Response(
                    {'detail': '权限不足'},
                    status=status.HTTP_403_FORBIDDEN
                )
            except TenantUser.DoesNotExist:
                return Response(
                    {'detail': '用户不在该租户中'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return _wrapped_view
    return decorator


def has_role_permission(role: str, permission_code: str) -> bool:
    """
    判断角色是否具有指定权限
    
    权限层级：
    - admin: 租户管理员，拥有所有权限
    - manager: 租户经理，拥有大部分管理权限
    - user: 普通用户，仅拥有基本访问权限
    """
    role_permissions = {
        'admin': [
            'tenant.user.view',
            'tenant.user.create',
            'tenant.user.update',
            'tenant.user.delete',
            'tenant.settings.view',
            'tenant.settings.update',
            'tenant.manage',
            'tenant.billing.view',
        ],
        'manager': [
            'tenant.user.view',
            'tenant.user.create',
            'tenant.user.update',
            'tenant.settings.view',
            'tenant.settings.update',
        ],
        'user': [
            'tenant.user.view',
        ]
    }
    
    # 管理员拥有所有权限
    if role == 'admin':
        return True
    
    return permission_code in role_permissions.get(role, [])


def get_user_tenant_role(user_id: int, tenant_id: int) -> Optional[str]:
    """
    获取用户在租户中的角色
    
    :param user_id: 用户ID
    :param tenant_id: 租户ID
    :return: 角色名称或 None
    """
    from dashboard.models import TenantUser
    
    try:
        tenant_user = TenantUser.objects.get(user_id=user_id, tenant_id=tenant_id)
        return tenant_user.role
    except TenantUser.DoesNotExist:
        return None


def is_tenant_admin(user_id: int, tenant_id: int) -> bool:
    """判断用户是否为租户管理员"""
    role = get_user_tenant_role(user_id, tenant_id)
    return role == 'admin'


def is_tenant_manager(user_id: int, tenant_id: int) -> bool:
    """判断用户是否为租户管理员或经理"""
    role = get_user_tenant_role(user_id, tenant_id)
    return role in ['admin', 'manager']


def can_access_tenant_resource(user_id: int, tenant_id: int) -> bool:
    """判断用户是否有权访问租户资源"""
    from dashboard.models import TenantUser
    
    try:
        TenantUser.objects.get(user_id=user_id, tenant_id=tenant_id, is_active=True)
        return True
    except TenantUser.DoesNotExist:
        return False
