import logging
from rest_framework import permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from ...models import ApiWhiteList
from ...serializers import ApiWhiteListSerializer
from ...filters import ApiWhiteListFilter
from ..base import BaseViewSet

import logging

logger = logging.getLogger(__name__)


class CustomPageNumberPagination(PageNumberPagination):
    """自定义分页类，支持pageSize参数"""
    # 默认的page_size参数
    page_size_query_param = 'page_size'
    # 默认每页显示10条记录
    page_size = 10
    # 最大每页显示100条记录
    max_page_size = 100
    
    def get_page_size(self, request):
        # 先检查是否有pageSize参数
        page_size = request.query_params.get('pageSize')
        if page_size:
            try:
                return min(int(page_size), self.max_page_size)
            except (TypeError, ValueError):
                pass
        # 如果没有pageSize参数或参数无效，则使用默认的page_size处理逻辑
        return super().get_page_size(request)


class ApiWhiteListViewSet(BaseViewSet):
    """API白名单视图集
    
    提供API白名单的CRUD操作，包括创建、查询、更新和删除API白名单信息
    """
    
    queryset = ApiWhiteList.objects.all()
    serializer_class = ApiWhiteListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ApiWhiteListFilter
    search_fields = ['url', 'method', 'enable_datasource']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    pagination_class = CustomPageNumberPagination
    
    # 操作模块名称
    operation_module = "接口白名单管理"

    # API白名单是系统级数据，不按租户过滤
    enable_tenant_filter = False
    
    def get_queryset(self):
        """获取API白名单查询集，优化查询性能
        
        Returns:
            QuerySet: 基础查询集，过滤逻辑由filter_queryset方法处理
        """
        # 调用父类方法获取基础查询集（包含数据权限过滤）
        queryset = super().get_queryset()
        
        # 优化查询，只选择必要的字段
        queryset = queryset.only(
            'id', 'url', 'method', 'enable_datasource', 'created_at'
        )
        
        return queryset
        
    def filter_queryset(self, queryset):
        """重写过滤方法，修复enable_datasource参数空值处理问题
        
        Args:
            queryset: 原始查询集
        
        Returns:
            QuerySet: 过滤后的查询集
        """
        # 检查enable_datasource参数
        enable_datasource = self.request.query_params.get('enable_datasource', None)
        
        # 如果enable_datasource参数存在但为空，则手动过滤，避免过滤掉所有数据
        if enable_datasource == '':
            # 先移除enable_datasource参数
            mutable_params = self.request.query_params.copy()
            mutable_params.pop('enable_datasource', None)
            
            # 临时保存原始的GET数据，使用修改后的参数
            original_get = self.request._request.GET
            self.request._request.GET = mutable_params
            
            try:
                # 调用父类的过滤方法
                filtered_queryset = super().filter_queryset(queryset)
            finally:
                # 恢复原始的GET数据
                self.request._request.GET = original_get
                
            return filtered_queryset
        
        # 正常情况下直接调用父类方法
        return super().filter_queryset(queryset)
    
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