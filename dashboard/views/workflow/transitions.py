"""
工作流流转记录视图
提供工作流流转记录的管理操作
"""
from rest_framework.decorators import action
from rest_framework.response import Response

from ...models import WorkflowTransition
from ...serializers import WorkflowTransitionSerializer
from ..base import BaseViewSet


class WorkflowTransitionViewSet(BaseViewSet):
    """工作流流转记录视图集"""
    
    queryset = WorkflowTransition.objects.all()
    serializer_class = WorkflowTransitionSerializer
    
    def get_queryset(self):
        """根据用户权限过滤"""
        user = self.request.user
        
        if user.is_superuser:
            return WorkflowTransition.objects.all()
        
        from ...models import TenantUser
        
        tenant_ids = TenantUser.objects.filter(
            user=user,
            is_active=True
        ).values_list('tenant_id', flat=True)
        
        return WorkflowTransition.objects.filter(tenant_id__in=tenant_ids)
    
    @action(detail=False, methods=['get'], url_path='task/(?P<task_id>[^/.]+)')
    def by_task(self, request, task_id=None):
        """获取指定任务的流转记录"""
        queryset = self.get_queryset().filter(task_id=task_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
