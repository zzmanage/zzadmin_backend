import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import QuerySet
from typing import Any, Dict, List, Optional, Union

from ..mixins import OperationLogMixin, ExportImportMixin, ExceptionHandlingMixin
from .mixins import TreeViewMixin
from ..mixins.filter_mixin import FilterMixin
from ..mixins.cache_mixin import CachedViewMixin

logger = logging.getLogger(__name__)


class BaseViewSet(ExceptionHandlingMixin, CachedViewMixin, OperationLogMixin, FilterMixin, ExportImportMixin, viewsets.ModelViewSet):
    """统一的基础视图集类，整合所有通用功能
    
    提供增强的通用功能，统一处理权限检查、数据过滤、查询集缓存和数据权限范围等逻辑
    减少各视图集的代码重复，提高可维护性
    """
    
    # 默认缓存过期时间（秒）
    DEFAULT_CACHE_TIMEOUT = 600  # 10分钟
    
    # 操作模块名称，子类需要覆盖
    operation_module = "基础模块"

    # 多租户：是否自动按用户所属租户过滤数据
    # 系统级数据（如菜单、权限、按钮等）应设为 False
    enable_tenant_filter = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置缓存策略为版本化缓存
        self.CACHE_STRATEGY_TYPE = 'versioned'
    
    def success_response(self, data=None, message="操作成功"):
        """统一的成功响应格式
        
        Args:
            data: 返回的数据
            message: 成功消息
            
        Returns:
            Response: 统一格式的成功响应
        """
        return Response({
            "code": 200,
            "message": message,
            "data": data or {}
        }, status=status.HTTP_200_OK)
    
    def error_response(self, message="操作失败", code=400):
        """统一的错误响应格式
        
        Args:
            message: 错误消息
            code: 错误码
            
        Returns:
            Response: 统一格式的错误响应
        """
        return Response({
            "code": code,
            "message": message,
            "data": {}
        }, status=code if 400 <= code < 600 else status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        """创建时自动设置创建人和租户"""
        save_kwargs = {}

        # 如果模型有 created_by 且未传入，自动设置
        model_class = getattr(serializer.Meta, 'model', None)
        if model_class and hasattr(model_class, 'created_by'):
            if 'created_by' not in serializer.validated_data:
                save_kwargs['created_by'] = self.request.user

        # 如果模型有 tenant 且已启用租户过滤，自动从请求上下文设置
        if model_class and hasattr(model_class, 'tenant') and self.enable_tenant_filter:
            if 'tenant' not in serializer.validated_data and self.request.user.is_authenticated:
                tenant_ids = list(self.request.user.user_tenants.values_list('tenant_id', flat=True))
                if len(tenant_ids) == 1:
                    from dashboard.models import Tenant
                    save_kwargs['tenant'] = Tenant.objects.get(id=tenant_ids[0])

        serializer.save(**save_kwargs)

    def create(self, request, *args, **kwargs):
        """统一的创建方法实现，添加缓存清除逻辑
        
        子类可以重写此方法以提供特定的创建逻辑，但应调用super().create()
        以确保缓存清除等通用功能正常工作
        """
        response = super().create(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response
    
    def update(self, request, *args, **kwargs):
        """统一的更新方法实现，添加缓存清除逻辑
        
        子类可以重写此方法以提供特定的更新逻辑，但应调用super().update()
        以确保缓存清除等通用功能正常工作
        """
        response = super().update(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response
    
    def destroy(self, request, *args, **kwargs):
        """统一的删除方法实现，添加缓存清除逻辑
        
        子类可以重写此方法以提供特定的删除逻辑，但应调用super().destroy()
        以确保缓存清除等通用功能正常工作
        """
        response = super().destroy(request, *args, **kwargs)
        if response.status_code < 400:
            self._invalidate_cache_on_update()
        return response
    
    def get_queryset(self):
        """增强的查询集获取方法，包含数据权限过滤和查询优化
        
        Returns:
            QuerySet: 处理后的查询集
        """
        # 先调用父类方法获取基础查询集（包含FilterMixin的过滤）
        queryset = super().get_queryset()
        
        # 应用数据权限过滤
        queryset = self._apply_data_permissions(queryset)
        
        # 优化查询，使用only限制字段
        queryset = self._optimize_query(queryset)
        
        return queryset
    
    def _apply_data_permissions(self, queryset: QuerySet) -> QuerySet:
        """应用数据权限过滤

        子类可以根据需要覆盖此方法，实现特定的数据权限逻辑

        Args:
            queryset: 原始查询集

        Returns:
            QuerySet: 应用数据权限过滤后的查询集
        """
        # 默认实现：如果用户不是超级用户，可以在这里添加数据权限过滤逻辑
        # 例如：基于用户所属部门、角色等进行数据过滤
        if hasattr(self, 'request') and hasattr(self.request, 'user'):
            user = self.request.user
            # 超级用户可以查看所有数据
            if user.is_superuser:
                return queryset

            # 多租户过滤：如果模型有 tenant 字段，按用户所属租户过滤
            if self.enable_tenant_filter and hasattr(queryset.model, 'tenant'):
                tenant_ids = list(user.user_tenants.values_list('tenant_id', flat=True))
                if tenant_ids:
                    queryset = queryset.filter(
                        tenant_id__in=tenant_ids
                    )
                else:
                    queryset = queryset.none()

        return queryset
    
    def _optimize_query(self, queryset: QuerySet) -> QuerySet:
        """优化查询性能
        
        子类可以覆盖此方法，添加特定的查询优化
        
        Args:
            queryset: 原始查询集
        
        Returns:
            QuerySet: 优化后的查询集
        """
        # 默认实现：尝试自动应用select_related优化
        # 子类应根据实际情况覆盖此方法，添加更具体的优化
        return queryset
    
    def list(self, request, *args, **kwargs):
        """增强的列表方法，使用父类的缓存机制
        
        Returns:
            Response: 列表数据响应
        """
        # 权限检查已在中间件中实现
        # 直接调用父类方法，它已经通过cache_response装饰器处理了缓存
        return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """增强的详情方法，使用父类的缓存机制
        
        Returns:
            Response: 详情数据响应
        """
        # 权限检查已在中间件中实现
        # 直接调用父类方法，它已经通过cache_response装饰器处理了缓存
        return super().retrieve(request, *args, **kwargs)


class TreeViewSet(BaseViewSet, TreeViewMixin):
    """树结构视图集基类，用于处理具有父子关系的数据模型
    
    整合了BaseViewSet的功能和TreeViewMixin的树结构处理能力
    """
    
    def tree(self, request, *args, **kwargs):
        """获取树结构数据，使用父类的缓存机制

        Returns:
            Response: 统一格式的树结构数据响应
        """
        # 权限检查由APIPermissionMiddleware统一处理
        
        try:
            # 获取所有活动状态的数据，使用select_related预加载关联关系
            queryset = self._get_tree_queryset()
            
            # 构建树结构
            tree_data = self._build_tree(queryset)
            
            # 使用统一的成功响应格式
            return self.success_response(data=tree_data, message=f"获取{self.operation_module}树结构成功")
        except Exception as e:
            logger.error(f"获取{self.operation_module}树结构失败: {str(e)}")
            # 使用统一的错误响应格式
            return self.error_response(message=f"获取{self.operation_module}树结构失败: {str(e)}", code=500)
    
    def _get_tree_queryset(self) -> QuerySet:
        """获取用于构建树结构的查询集
        
        子类可以覆盖此方法来定制查询逻辑
        
        Returns:
            QuerySet: 用于构建树结构的查询集
        """
        return self.queryset.filter(status=True).order_by("sort", "id").select_related('parent')
    
    def _optimize_query(self, queryset: QuerySet) -> QuerySet:
        """优化树结构查询性能
        
        Args:
            queryset: 原始查询集
        
        Returns:
            QuerySet: 优化后的查询集
        """
        # 树结构查询优化，预加载父节点关系
        return queryset.select_related('parent')


class ReadOnlyViewSet(CachedViewMixin, viewsets.ReadOnlyModelViewSet):
    """只读视图集，只提供GET操作
    
    适用于不需要修改操作的场景
    """
    
    # 默认缓存过期时间（秒）
    DEFAULT_CACHE_TIMEOUT = 600  # 10分钟
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化时自动设置缓存支持
        self._auto_setup_cache_for_readonly_views()

