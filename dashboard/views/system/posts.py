import logging
from rest_framework import permissions, filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from ...models import Post
from ...serializers import PostSerializer
from ...filters import PostFilter
from ..base import BaseViewSet

logger = logging.getLogger(__name__)


class PostViewSet(BaseViewSet):
    """岗位视图集
    
    提供岗位的CRUD操作，包括创建、查询、更新和删除岗位信息
    """
    
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PostFilter
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['sort', 'created_at', 'updated_at']
    ordering = ['sort']
    
    # 操作模块名称
    operation_module = "岗位管理"
    
    @action(detail=False, methods=['get'])
    def all_list(self, request):
        """获取全量岗位数据（不分页）
        
        用于在用户编辑页面中选择岗位时，获取系统中所有可用的岗位列表
        
        Returns:
            Response: 包含所有岗位的列表数据
        """
        # 获取所有状态为启用的岗位
        posts = Post.objects.filter(status=True).order_by('sort')
        # 使用序列化器序列化数据
        serializer = self.get_serializer(posts, many=True)
        # 记录操作日志
        return Response({
            'success': True,
            'results': serializer.data
        })