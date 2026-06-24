"""
工作流任务视图
提供工作流任务的管理操作
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from ...models import WorkflowTask, WorkflowTransition
from ...serializers import WorkflowTaskSerializer, WorkflowTaskActionSerializer
from ..base import BaseViewSet
from ...workflow.engine import WorkflowEngine


class WorkflowTaskViewSet(BaseViewSet):
    """工作流任务视图集"""
    
    queryset = WorkflowTask.objects.all()
    serializer_class = WorkflowTaskSerializer
    
    def get_queryset(self):
        """根据用户权限过滤"""
        user = self.request.user
        
        if user.is_superuser:
            return WorkflowTask.objects.all()
        
        from ...models import TenantUser
        
        tenant_ids = TenantUser.objects.filter(
            user=user,
            is_active=True
        ).values_list('tenant_id', flat=True)
        
        return WorkflowTask.objects.filter(tenant_id__in=tenant_ids)
    
    @action(detail=True, methods=['post'], url_path='execute')
    def execute_action(self, request, pk=None):
        """执行任务操作（兼容旧接口）"""
        task = self.get_object()
        serializer = WorkflowTaskActionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action_type = serializer.validated_data['action']
        comment = serializer.validated_data.get('comment', '')
        data = serializer.validated_data.get('data', {})
        
        if action_type == 'claim':
            # 使用流程引擎认领任务
            try:
                WorkflowEngine.claim_task(pk, request.user, comment)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif action_type == 'complete':
            # 使用流程引擎完成任务（会自动推进流程）
            WorkflowEngine.complete_task(pk, request.user, comment, data)
        elif action_type == 'reject':
            # 使用流程引擎拒绝任务
            WorkflowEngine.reject_task(pk, request.user, comment, data)
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='claim')
    def claim(self, request, pk=None):
        """认领任务（独立端点）"""
        task = self.get_object()
        
        if task.status != 0:
            return Response({'error': '任务状态不允许认领'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            WorkflowEngine.claim_task(pk, request.user, request.data.get('comment'))
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """完成任务并推进流程（独立端点）"""
        task = self.get_object()
        
        if task.status not in [0, 1]:
            return Response({'error': '任务状态不允许完成'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            WorkflowEngine.complete_task(
                pk, 
                request.user, 
                request.data.get('comment'), 
                request.data.get('data')
            )
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """拒绝任务（独立端点）"""
        task = self.get_object()
        
        try:
            WorkflowEngine.reject_task(
                pk, 
                request.user, 
                request.data.get('comment'), 
                request.data.get('data')
            )
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """获取待处理的任务"""
        queryset = self.get_queryset().filter(status=0)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        """获取当前用户的任务"""
        queryset = self.get_queryset().filter(assignee=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='unassigned')
    def unassigned(self, request):
        """获取未分配的任务"""
        queryset = self.get_queryset().filter(assignee__isnull=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
