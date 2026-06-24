"""
工作流定义视图
提供工作流定义的CRUD操作
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from ...models import WorkflowDefinition
from ...serializers import WorkflowDefinitionSerializer
from ..base import BaseViewSet


class WorkflowDefinitionViewSet(BaseViewSet):
    """工作流定义视图集"""
    
    queryset = WorkflowDefinition.objects.all()
    serializer_class = WorkflowDefinitionSerializer
    
    def get_queryset(self):
        """根据用户权限过滤"""
        user = self.request.user
        
        if user.is_superuser:
            return WorkflowDefinition.objects.all()
        
        from ...models import TenantUser
        
        tenant_ids = TenantUser.objects.filter(
            user=user,
            is_active=True
        ).values_list('tenant_id', flat=True)
        
        return WorkflowDefinition.objects.filter(tenant_id__in=tenant_ids)
    
    def create(self, request, *args, **kwargs):
        """创建工作流定义"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 设置创建人
        serializer.validated_data['created_by'] = request.user
        
        instance = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['put'])
    def activate(self, request, pk=None):
        """激活工作流定义"""
        definition = self.get_object()
        definition.status = 1
        definition.save()
        serializer = self.get_serializer(definition)
        return Response(serializer.data)
    
    @action(detail=True, methods=['put'])
    def deactivate(self, request, pk=None):
        """停用工作流定义"""
        definition = self.get_object()
        definition.status = 0
        definition.save()
        serializer = self.get_serializer(definition)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """切换工作流状态（启用/禁用）"""
        definition = self.get_object()
        definition.status = 1 - definition.status
        definition.save()
        serializer = self.get_serializer(definition)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """获取所有激活的工作流定义"""
        queryset = self.get_queryset().filter(status=1)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
