import logging
from rest_framework import permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ...models import MenuButton
from ...serializers import MenuButtonSerializer
from ...filters import MenuButtonFilter
from ..base import BaseViewSet

logger = logging.getLogger(__name__)


class MenuButtonViewSet(BaseViewSet):
    """菜单按钮视图集
    
    提供菜单按钮的CRUD操作，包括创建、查询、更新和删除菜单按钮信息
    """
    
    queryset = MenuButton.objects.all()
    serializer_class = MenuButtonSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MenuButtonFilter
    search_fields = ['name', 'value', 'api']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    # 操作模块名称
    operation_module = "菜单按钮管理"

    # 菜单按钮是系统级数据，不按租户过滤
    enable_tenant_filter = False
    
    def get_queryset(self):
        """获取菜单按钮查询集，优化查询性能
        
        Returns:
            QuerySet: 过滤后的菜单按钮查询集
        """
        # 记录调试信息
        logger.debug(f"MenuButtonViewSet.get_queryset: pk={self.kwargs.get('pk')}, request method={self.request.method}")
        
        # 当获取单个对象详情时（如menu_buttons/5/），直接返回原始查询集不使用缓存
        if self.kwargs.get('pk'):
            logger.debug(f"获取单个对象详情，pk={self.kwargs.get('pk')}")
            queryset = super().get_queryset()
            logger.debug(f"查询结果数量: {queryset.count()}")
            return queryset
            
        # 构建缓存键，使用基类的方法
        cache_key = self.get_cache_key('queryset', **{
            'user_id': self.request.user.id,
            'params': self.request.GET.urlencode()
        })
        
        # 尝试从缓存获取数据
        cached_queryset = self._get_cached_data(cache_key)
        if cached_queryset:
            logger.debug(f"使用缓存数据，cache_key={cache_key}")
            return cached_queryset

        # 限制查询字段，只获取必要的信息
        queryset = super().get_queryset().only(
            'id', 'name', 'value', 'menu_id', 'api', 'method',
            'created_at', 'updated_at'
        )

        # 缓存查询结果，有效期1分钟
        self._set_cached_data(cache_key, queryset, 60)
        
        logger.debug(f"查询完成，返回结果数量: {queryset.count()}")

        return queryset

    def create(self, request, *args, **kwargs):
        """重写创建方法，添加缓存清除逻辑"""
        response = super().create(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response
    
    def update(self, request, *args, **kwargs):
        """重写更新方法，添加缓存清除逻辑"""
        response = super().update(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response
    
    def retrieve(self, request, *args, **kwargs):
        """重写获取单个对象方法，添加详细的调试日志"""
        logger.debug(f"MenuButtonViewSet.retrieve: 尝试获取ID为{kwargs.get('pk')}的菜单按钮")
        
        # 使用父类的retrieve方法，它已经有异常处理机制
        instance = self.get_object()
        logger.debug(f"MenuButtonViewSet.retrieve: 成功获取ID为{kwargs.get('pk')}的菜单按钮")
        
        serializer = self.get_serializer(instance)
        logger.debug(f"MenuButtonViewSet.retrieve: 成功序列化ID为{kwargs.get('pk')}的菜单按钮")
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """重写删除方法，添加缓存清除逻辑"""
        response = super().destroy(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response