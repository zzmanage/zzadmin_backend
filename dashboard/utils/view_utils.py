import logging
from rest_framework import status
from rest_framework.response import Response

from .cache_utils import CacheManager

logger = logging.getLogger(__name__)


class CachedQuerySetMixin:
    """缓存查询集混入类

    提供查询集缓存功能，减少数据库查询
    """
    
    def __init__(self):
        # 初始化缓存管理器
        self.cache_manager = CacheManager(prefix='queryset', default_timeout=300)
        
    def get_cached_queryset(self, cache_key, queryset_func, timeout=None):
        """获取缓存的查询集

        Args:
            cache_key: 缓存键
            queryset_func: 获取查询集的函数
            timeout: 缓存过期时间（秒），默认为None（使用默认超时）

        Returns:
            QuerySet: 查询结果
        """
        # 尝试从缓存获取
        cached_queryset = self.cache_manager.get(cache_key)
        if cached_queryset:
            return cached_queryset
        
        # 执行查询
        queryset = queryset_func()
        
        # 缓存查询结果，使用提供的超时或默认超时
        self.cache_manager.set(cache_key, queryset, timeout)
        
        return queryset