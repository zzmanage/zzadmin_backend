import logging
from rest_framework import permissions
from rest_framework.viewsets import ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache

from ...models import OperationLog
from ...serializers import OperationLogSerializer
from ...filters import OperationLogFilter
from ..base import ReadOnlyViewSet

logger = logging.getLogger(__name__)


class OperationLogViewSet(ReadOnlyViewSet):
    """操作日志视图集
    
    提供只读接口，用于查看和过滤操作日志信息
    """
    
    queryset = OperationLog.objects.all().order_by("-created_at")
    serializer_class = OperationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OperationLogFilter
    
    # 操作模块名称
    operation_module = "操作日志管理"
    
    def get_queryset(self):
        """获取操作日志查询集，支持按用户ID、操作类型、模型名称和日期范围过滤

        Returns:
            QuerySet: 过滤后的操作日志查询集
        """
        queryset = super().get_queryset()
        # 多租户过滤
        user = self.request.user
        if not user.is_superuser:
            tenant_ids = list(user.user_tenants.values_list('tenant_id', flat=True))
            if tenant_ids:
                queryset = queryset.filter(tenant_id__in=tenant_ids)
            else:
                queryset = queryset.none()
        
        # 支持过滤
        user_id = self.request.query_params.get("user_id")
        action = self.request.query_params.get("action")
        model = self.request.query_params.get("model")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)
        if model:
            queryset = queryset.filter(model=model)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset
    
    def filter_queryset(self, queryset):
        """应用过滤器处理查询集
        
        Returns:
            QuerySet: 过滤后的操作日志查询集
        """
        # 直接调用父类方法应用过滤器
        # 缓存逻辑由CachedViewMixin在list/retrieve方法中统一处理
        return super().filter_queryset(queryset)