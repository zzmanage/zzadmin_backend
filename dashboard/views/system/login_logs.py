import logging
from rest_framework import permissions
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache

from ...models import LoginLog
from ...serializers import LoginLogSerializer
from ...filters import LoginLogFilter
from ..base import ReadOnlyViewSet

logger = logging.getLogger(__name__)


class LoginLogViewSet(ReadOnlyViewSet):
    """登录日志视图集
    
    提供只读接口，用于查看和过滤登录日志信息
    """
    
    queryset = LoginLog.objects.all().order_by("-created_at")
    serializer_class = LoginLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LoginLogFilter
    
    # 操作模块名称
    operation_module = "登录日志管理"
    
    def get_queryset(self):
        """获取登录日志查询集，支持按用户名、IP和日期范围过滤

        Returns:
            QuerySet: 过滤后的登录日志查询集
        """
        # 从父类获取查询集并添加字段限制，使用模型中实际存在的字段
        queryset = super().get_queryset().only('id', 'username', 'ip',
                                               'agent', 'browser', 'os', 'country',
                                               'province', 'city', 'created_at')
        # 多租户过滤
        user = self.request.user
        if not user.is_superuser:
            tenant_ids = list(user.user_tenants.values_list('tenant_id', flat=True))
            if tenant_ids:
                queryset = queryset.filter(tenant_id__in=tenant_ids)
            else:
                queryset = queryset.none()
        return queryset

    def filter_queryset(self, queryset):
        """应用过滤器并缓存结果
        
        Returns:
            QuerySet: 过滤后的登录日志查询集
        """
        user = self.request.user
        # 缓存键，包含用户ID和请求参数
        cache_key = f'login_log_queryset_{user.id}_{self.request.GET.urlencode()}'
        # 尝试从缓存获取数据
        cached_queryset = cache.get(cache_key)
        if cached_queryset:
            return cached_queryset

        # 应用过滤器
        filtered_queryset = super().filter_queryset(queryset)

        # 缓存过滤后的结果1分钟
        cache.set(cache_key, filtered_queryset, 60)

        return filtered_queryset