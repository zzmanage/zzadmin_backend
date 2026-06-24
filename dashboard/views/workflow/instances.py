"""
工作流实例视图
提供工作流实例的管理操作
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from ...models import WorkflowInstance, WorkflowDefinition
from ...serializers import WorkflowInstanceSerializer
from ..base import BaseViewSet
from ...workflow.engine import WorkflowEngine


class WorkflowInstanceViewSet(BaseViewSet):
    """工作流实例视图集"""
    
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer
    
    def get_queryset(self):
        """根据用户权限过滤"""
        user = self.request.user
        
        if user.is_superuser:
            return WorkflowInstance.objects.all()
        
        from ...models import TenantUser
        
        tenant_ids = TenantUser.objects.filter(
            user=user,
            is_active=True
        ).values_list('tenant_id', flat=True)
        
        return WorkflowInstance.objects.filter(tenant_id__in=tenant_ids)
    
    def create(self, request, *args, **kwargs):
        """创建工作流实例（启动流程）"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.validated_data['created_by'] = request.user
        
        instance = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['put'])
    def start(self, request, pk=None):
        """启动工作流实例"""
        instance = self.get_object()
        instance.status = 1  # 运行中
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成工作流实例"""
        instance = self.get_object()
        instance.status = 2  # 已完成
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='start')
    def start_workflow(self, request):
        """启动流程实例（使用流程引擎，自动创建初始任务）"""
        # 获取流程定义ID
        definition_id = request.data.get('definition_id') or request.data.get('definition')
        
        if not definition_id:
            return Response({'error': '缺少流程定义ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 使用流程引擎启动流程
            instance = WorkflowEngine.start_workflow(
                definition_id=definition_id,
                user=request.user,
                business_key=request.data.get('business_key'),
                data=request.data.get('data')
            )
            
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except WorkflowDefinition.DoesNotExist:
            return Response({'error': '流程定义不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='running')
    def running(self, request):
        """获取所有运行中的工作流实例"""
        queryset = self.get_queryset().filter(status=1)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='completed')
    def completed(self, request):
        """获取所有已完成的工作流实例"""
        queryset = self.get_queryset().filter(status=2)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        """获取当前用户创建的工作流实例"""
        queryset = self.get_queryset().filter(created_by=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
