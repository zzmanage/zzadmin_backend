"""
租户用户管理视图
提供租户用户关联的管理操作
"""
from rest_framework.response import Response
from rest_framework.decorators import action

from ...models import TenantUser
from ...serializers import TenantUserSerializer
from ..base import BaseViewSet


class TenantUserViewSet(BaseViewSet):
    """租户用户关联视图集"""
    
    queryset = TenantUser.objects.all()
    serializer_class = TenantUserSerializer
    
    def get_queryset(self):
        """根据用户权限过滤"""
        user = self.request.user
        if user.is_superuser:
            return TenantUser.objects.all()
        
        tenant_ids = TenantUser.objects.filter(
            user=user,
            is_active=True
        ).values_list('tenant_id', flat=True)
        
        return TenantUser.objects.filter(tenant_id__in=tenant_ids)
    
    @action(detail=False, methods=['get'], url_path='my_roles')
    def my_roles(self, request):
        """获取当前用户在各租户中的角色"""
        user = request.user
        
        tenant_roles = TenantUser.objects.filter(
            user=user,
            is_active=True
        ).select_related('tenant')
        
        result = []
        for tu in tenant_roles:
            result.append({
                'tenant_id': tu.tenant_id,
                'tenant_name': tu.tenant.name,
                'tenant_code': tu.tenant.code,
                'role': tu.role,
                'joined_at': tu.joined_at
            })
        
        return Response(result)
