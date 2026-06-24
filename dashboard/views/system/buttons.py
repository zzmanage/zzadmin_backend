import logging
from rest_framework import permissions, filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ...models import Button
from ...serializers import ButtonSerializer
from ...filters import ButtonFilter
from ..base import BaseViewSet

import logging

logger = logging.getLogger(__name__)


class ButtonViewSet(BaseViewSet):
    """按钮视图集
    
    提供按钮的CRUD操作，包括创建、查询、更新和删除按钮信息
    """
    
    queryset = Button.objects.all()
    serializer_class = ButtonSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ButtonFilter
    search_fields = ['name', 'value']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    # 操作模块名称
    operation_module = "按钮管理"

    # 按钮是系统级数据，不按租户过滤
    enable_tenant_filter = False
    
    def get_queryset(self):
        """获取按钮查询集，优化查询性能
        
        Returns:
            QuerySet: 过滤后的按钮查询集
        """
        # 构建缓存键，使用基类的方法
        cache_key = self.get_cache_key('queryset', **{
            'user_id': self.request.user.id,
            'params': self.request.GET.urlencode()
        })
        
        # 尝试从缓存获取数据
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # 限制查询字段，只获取必要的信息
        queryset = super().get_queryset().only(
            'id', 'name', 'value',
            'created_at', 'updated_at'
        )

        # 缓存查询结果
        self._set_cached_data(cache_key, queryset, 60)  # 缓存1分钟

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
    
    def destroy(self, request, *args, **kwargs):
        """重写删除方法，添加缓存清除逻辑"""
        response = super().destroy(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response
        
    @action(detail=False, methods=['get'])  
    def all(self, request):
        """获取全量按钮列表（非分页）"""
        try:
            # 权限检查已在中间件中实现
            
            # 构建缓存键
            cache_key = self.get_cache_key('all_buttons')
            
            # 尝试从缓存获取数据
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return Response(cached_data)
                
            # 获取所有按钮数据，使用only优化性能
            buttons = Button.objects.all().only('id', 'name', 'value')
            serializer = ButtonSerializer(buttons, many=True)
            
            # 缓存结果
            self._set_cached_data(cache_key, serializer.data)
            
            # 返回序列化后的数据
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"获取全量按钮列表失败: {str(e)}")
            return Response({'error': '获取全量按钮列表失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["post"], url_path="refresh_cache")
    def refresh_cache(self, request):
        """刷新所有按钮缓存
        
        Returns:
            Response: 刷新结果信息
        """
        try:
            # 清除所有按钮相关缓存
            self._invalidate_cache_on_update()
            logger.info("按钮缓存已成功刷新")
            return Response(
                {"detail": "按钮缓存已成功刷新"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"刷新按钮缓存失败: {str(e)}")
            return Response(
                {"error": "刷新按钮缓存失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)