"""
租户管理视图
提供租户的CRUD操作
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from django.contrib.auth.models import User

from ...models import Tenant, TenantSetting
from ...serializers import TenantSerializer, TenantSettingSerializer
from ...utils import set_current_tenant, get_current_tenant_id, is_tenant_admin
from ..base import BaseViewSet


class TenantViewSet(BaseViewSet):
    """租户管理视图集"""
    
    queryset = Tenant.all_objects.all()
    serializer_class = TenantSerializer
    
    def get_queryset(self):
        """根据用户权限过滤租户"""
        user = self.request.user
        
        if user.is_superuser:
            return Tenant.all_objects.all()
        
        from ...models import TenantUser
        
        user_tenants = TenantUser.objects.filter(user=user, is_active=True)
        tenant_ids = user_tenants.values_list('tenant_id', flat=True)
        return Tenant.all_objects.filter(id__in=tenant_ids)
    
    def create(self, request, *args, **kwargs):
        """创建租户，自动记录创建人并添加为租户管理员"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.validated_data['created_by'] = request.user
        
        tenant = serializer.save()
        
        set_current_tenant(tenant.id)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """获取租户用户列表"""
        tenant = self.get_object()
        
        set_current_tenant(tenant.id)
        
        from ...models import TenantUser
        
        tenant_users = TenantUser.objects.filter(tenant=tenant)
        tenant_user_map = {tu.user_id: tu.role for tu in tenant_users}
        
        all_users = User.objects.all()
        
        result = []
        for user in all_users:
            result.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'tenantRole': tenant_user_map.get(user.id)
            })
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def add_users(self, request, pk=None):
        """批量添加用户到租户"""
        tenant = self.get_object()
        user_ids = request.data.get('user_ids', [])
        default_role = request.data.get('role', 'user')
        
        if default_role not in ['admin', 'manager', 'user']:
            return Response({'detail': '无效的角色'}, status=status.HTTP_400_BAD_REQUEST)
        
        from ...models import TenantUser
        
        added_count = 0
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                if not TenantUser.objects.filter(tenant=tenant, user=user).exists():
                    TenantUser.objects.create(
                        tenant=tenant,
                        user=user,
                        role=default_role
                    )
                    added_count += 1
            except User.DoesNotExist:
                continue
        
        return Response({'detail': f'成功添加 {added_count} 个用户'}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['put', 'delete'], url_path='users/(?P<user_id>[^/.]+)')
    def user_management(self, request, pk=None, user_id=None):
        """管理租户用户（更新角色或移除）"""
        tenant = self.get_object()
        
        if not request.user.is_superuser and not is_tenant_admin(request.user.id, tenant.id):
            return Response({'detail': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
        
        from ...models import TenantUser
        
        try:
            tenant_user = TenantUser.objects.get(tenant=tenant, user_id=user_id)
        except TenantUser.DoesNotExist:
            return Response({'detail': '用户不在该租户中'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'PUT':
            role = request.data.get('role')
            if role not in ['admin', 'manager', 'user']:
                return Response({'detail': '无效的角色'}, status=status.HTTP_400_BAD_REQUEST)
            tenant_user.role = role
            tenant_user.save()
            from ...serializers import TenantUserSerializer
            serializer = TenantUserSerializer(tenant_user)
            return Response(serializer.data)
        elif request.method == 'DELETE':
            tenant_user.delete()
            return Response({'detail': '已移除'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get', 'put'])
    def tenant_settings(self, request, pk=None):
        """获取或更新租户配置"""
        tenant = self.get_object()
        
        if request.method == 'GET':
            setting, _ = TenantSetting.objects.get_or_create(tenant=tenant)
            serializer = TenantSettingSerializer(setting)
            return Response(serializer.data)
        elif request.method == 'PUT':
            if not request.user.is_superuser and not is_tenant_admin(request.user.id, tenant.id):
                return Response({'detail': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
            
            setting, _ = TenantSetting.objects.get_or_create(tenant=tenant)
            serializer = TenantSettingSerializer(setting, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='me')
    def current(self, request):
        """获取当前租户信息（根据请求上下文）"""
        tenant_id = get_current_tenant_id()
        
        if not tenant_id:
            return Response({'detail': '未找到租户上下文'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            tenant = Tenant.all_objects.get(id=tenant_id)
            serializer = TenantSerializer(tenant)
            return Response(serializer.data)
        except Tenant.DoesNotExist:
            return Response({'detail': '租户不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        """获取当前用户所属的所有租户"""
        user = request.user
        
        if user.is_superuser:
            tenants = Tenant.all_objects.filter(status=1)
        else:
            from ...models import TenantUser
            
            tenant_ids = TenantUser.objects.filter(
                user=user,
                is_active=True
            ).values_list('tenant_id', flat=True)
            tenants = Tenant.all_objects.filter(id__in=tenant_ids, status=1)
        
        serializer = TenantSerializer(tenants, many=True)
        return Response(serializer.data)
