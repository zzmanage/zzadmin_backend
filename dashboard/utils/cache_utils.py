import logging
import time
from typing import Any, Optional, Union, Callable
from django.core.cache import cache
from django.utils.functional import wraps

logger = logging.getLogger(__name__)


def safe_delete_pattern(pattern: str) -> bool:
    """安全地删除符合模式的缓存，兼容不同的缓存后端
    
    Args:
        pattern: 缓存键模式，支持通配符
    
    Returns:
        bool: 是否成功执行删除操作
    """
    try:
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(pattern)
            return True
        else:
            logger.debug(f"当前缓存后端不支持delete_pattern方法，模式: {pattern}")
            return False
    except Exception as e:
        logger.warning(f"删除缓存模式失败: {pattern}, 错误: {str(e)}")
        return False


def safe_delete_many_by_pattern(pattern: str) -> int:
    """通过模式安全地删除多个缓存，使用keys方法作为备选方案
    
    Args:
        pattern: 缓存键模式
    
    Returns:
        int: 成功删除的缓存数量
    """
    deleted_count = 0
    
    # 首先尝试使用delete_pattern方法
    if safe_delete_pattern(pattern):
        # delete_pattern方法不返回删除数量，返回一个估计值
        return -1  # 表示使用了delete_pattern方法
    
    # 如果不支持delete_pattern，尝试使用keys方法
    try:
        if hasattr(cache, 'keys'):
            cache_keys = [key for key in cache.keys(pattern)]
            if cache_keys:
                cache.delete_many(cache_keys)
                deleted_count = len(cache_keys)
                logger.debug(f"通过keys方法删除了{deleted_count}个缓存项，模式: {pattern}")
    except Exception as e:
        logger.warning(f"通过keys方法删除缓存失败: {pattern}, 错误: {str(e)}")
    
    return deleted_count


class CacheManager:
    """统一的缓存管理类，提供缓存操作的封装和统计功能"""
    
    def __init__(self, prefix: str = "", default_timeout: int = 3600):
        """初始化缓存管理器
        
        Args:
            prefix: 缓存键前缀
            default_timeout: 默认缓存超时时间（秒）
        """
        self.prefix = prefix
        self.default_timeout = default_timeout
        
        # 缓存统计信息
        self._stats = {
            'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
            'set': {'count': 0, 'total_time': 0.0},
            'delete': {'count': 0, 'total_time': 0.0},
            'delete_pattern': {'count': 0, 'total_time': 0.0, 'success': 0},
            'delete_many': {'count': 0, 'total_time': 0.0, 'items': 0},
            'errors': {'get': 0, 'set': 0, 'delete': 0, 'delete_pattern': 0}
        }
        
        # 按策略类型的统计信息
        self._strategy_stats = {}
    
    def add_get(self, strategy_type: str = 'base', hit: bool = False, elapsed: float = 0.0) -> None:
        """记录缓存获取操作的统计信息
        
        Args:
            strategy_type: 缓存策略类型
            hit: 是否命中缓存
            elapsed: 操作耗时（秒）
        """
        # 更新总体统计
        self._stats['get']['total_time'] += elapsed
        if hit:
            self._stats['get']['hits'] += 1
        else:
            self._stats['get']['misses'] += 1
        
        # 更新策略类型统计
        if strategy_type not in self._strategy_stats:
            self._strategy_stats[strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'delete': {'count': 0, 'total_time': 0.0},
                'invalidation': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'delete': 0, 'invalidation': 0}
            }
        
        self._strategy_stats[strategy_type]['get']['total_time'] += elapsed
        if hit:
            self._strategy_stats[strategy_type]['get']['hits'] += 1
        else:
            self._strategy_stats[strategy_type]['get']['misses'] += 1
    
    def add_set(self, strategy_type: str = 'base', elapsed: float = 0.0) -> None:
        """记录缓存设置操作的统计信息
        
        Args:
            strategy_type: 缓存策略类型
            elapsed: 操作耗时（秒）
        """
        # 更新总体统计
        self._stats['set']['count'] += 1
        self._stats['set']['total_time'] += elapsed
        
        # 更新策略类型统计
        if strategy_type not in self._strategy_stats:
            self._strategy_stats[strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'delete': {'count': 0, 'total_time': 0.0},
                'invalidation': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'delete': 0, 'invalidation': 0}
            }
        
        self._strategy_stats[strategy_type]['set']['count'] += 1
        self._strategy_stats[strategy_type]['set']['total_time'] += elapsed
    
    def add_delete(self, strategy_type: str = 'base', elapsed: float = 0.0) -> None:
        """记录缓存删除操作的统计信息
        
        Args:
            strategy_type: 缓存策略类型
            elapsed: 操作耗时（秒）
        """
        # 更新总体统计
        self._stats['delete']['count'] += 1
        self._stats['delete']['total_time'] += elapsed
        
        # 更新策略类型统计
        if strategy_type not in self._strategy_stats:
            self._strategy_stats[strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'delete': {'count': 0, 'total_time': 0.0},
                'invalidation': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'delete': 0, 'invalidation': 0}
            }
        
        self._strategy_stats[strategy_type]['delete']['count'] += 1
        self._strategy_stats[strategy_type]['delete']['total_time'] += elapsed
    
    def add_invalidation(self, strategy_type: str = 'base', elapsed: float = 0.0) -> None:
        """记录缓存失效操作的统计信息
        
        Args:
            strategy_type: 缓存策略类型
            elapsed: 操作耗时（秒）
        """
        # 更新策略类型统计
        if strategy_type not in self._strategy_stats:
            self._strategy_stats[strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'delete': {'count': 0, 'total_time': 0.0},
                'invalidation': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'delete': 0, 'invalidation': 0}
            }
        
        self._strategy_stats[strategy_type]['invalidation']['count'] += 1
        self._strategy_stats[strategy_type]['invalidation']['total_time'] += elapsed
    
    def add_error(self, strategy_type: str = 'base', operation: str = 'get') -> None:
        """记录缓存操作的错误信息
        
        Args:
            strategy_type: 缓存策略类型
            operation: 操作类型（get/set/delete/invalidation）
        """
        # 更新总体统计
        if operation in self._stats['errors']:
            self._stats['errors'][operation] += 1
        
        # 更新策略类型统计
        if strategy_type not in self._strategy_stats:
            self._strategy_stats[strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'delete': {'count': 0, 'total_time': 0.0},
                'invalidation': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'delete': 0, 'invalidation': 0}
            }
        
        if operation in self._strategy_stats[strategy_type]['errors']:
            self._strategy_stats[strategy_type]['errors'][operation] += 1
    
    def get_stats(self) -> dict:
        """获取缓存统计信息
        
        Returns:
            dict: 统计信息字典
        """
        return {
            'summary': self._stats,
            'by_strategy': self._strategy_stats
        }
    
    def reset_stats(self) -> None:
        """重置缓存统计信息"""
        self._stats = {
            'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
            'set': {'count': 0, 'total_time': 0.0},
            'delete': {'count': 0, 'total_time': 0.0},
            'delete_pattern': {'count': 0, 'total_time': 0.0, 'success': 0},
            'delete_many': {'count': 0, 'total_time': 0.0, 'items': 0},
            'errors': {'get': 0, 'set': 0, 'delete': 0, 'delete_pattern': 0}
        }
        self._strategy_stats = {}
    
    def get_key(self, key: str, **kwargs) -> str:
        """生成带前缀的完整缓存键
        
        Args:
            key: 基础缓存键
            **kwargs: 额外参数，用于格式化缓存键
        
        Returns:
            str: 完整的缓存键
        """
        full_key = f"{self.prefix}_{key}" if self.prefix else key
        if kwargs:
            return full_key.format(**kwargs)
        return full_key
    
    def get(self, key: str, default: Any = None, **kwargs) -> Any:
        """获取缓存值，记录统计信息
        
        Args:
            key: 缓存键
            default: 默认值
            **kwargs: 用于格式化缓存键的参数
        
        Returns:
            Any: 缓存值或默认值
        """
        cache_key = self.get_key(key, **kwargs)
        start_time = time.time()
        try:
            value = cache.get(cache_key, default)
            elapsed = time.time() - start_time
            # 记录基本统计信息
            self.add_get(strategy_type='base', hit=(value is not None), elapsed=elapsed)
            return value
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"获取缓存失败: {cache_key}, 错误: {str(e)}")
            # 记录错误统计
            self.add_error(strategy_type='base', operation='get')
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None, **kwargs) -> None:
        """设置缓存值，记录统计信息
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 超时时间（秒），None表示使用默认值
            **kwargs: 用于格式化缓存键的参数
        """
        cache_key = self.get_key(key, **kwargs)
        actual_timeout = timeout if timeout is not None else self.default_timeout
        start_time = time.time()
        try:
            cache.set(cache_key, value, actual_timeout)
            elapsed = time.time() - start_time
            # 记录基本统计信息
            self.add_set(strategy_type='base', elapsed=elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"设置缓存失败: {cache_key}, 错误: {str(e)}")
            # 记录错误统计
            self.add_error(strategy_type='base', operation='set')
    
    def delete(self, key: str, **kwargs) -> None:
        """删除单个缓存，记录统计信息
        
        Args:
            key: 缓存键
            **kwargs: 用于格式化缓存键的参数
        """
        cache_key = self.get_key(key, **kwargs)
        start_time = time.time()
        try:
            cache.delete(cache_key)
            elapsed = time.time() - start_time
            # 记录基本统计信息
            self.add_delete(strategy_type='base', elapsed=elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"删除缓存失败: {cache_key}, 错误: {str(e)}")
            # 记录错误统计
            self.add_error(strategy_type='base', operation='delete')
    
    def delete_pattern(self, pattern: str, **kwargs) -> bool:
        """删除符合模式的缓存，记录统计信息
        
        Args:
            pattern: 缓存键模式
            **kwargs: 用于格式化模式的参数
        
        Returns:
            bool: 是否成功执行删除操作
        """
        full_pattern = self.get_key(pattern, **kwargs)
        start_time = time.time()
        try:
            result = safe_delete_pattern(full_pattern)
            elapsed = time.time() - start_time
            # 记录基本统计信息
            self._stats['delete_pattern']['count'] += 1
            self._stats['delete_pattern']['total_time'] += elapsed
            if result:
                self._stats['delete_pattern']['success'] += 1
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"删除模式缓存失败: {full_pattern}, 错误: {str(e)}")
            # 记录错误统计
            self._stats['delete_pattern']['count'] += 1
            self._stats['delete_pattern']['total_time'] += elapsed
            self.add_error(strategy_type='base', operation='delete_pattern')
            return False
    
    def delete_many_by_pattern(self, pattern: str, **kwargs) -> int:
        """通过模式删除多个缓存，记录统计信息
        
        Args:
            pattern: 缓存键模式
            **kwargs: 用于格式化模式的参数
        
        Returns:
            int: 成功删除的缓存数量
        """
        full_pattern = self.get_key(pattern, **kwargs)
        start_time = time.time()
        try:
            deleted_count = safe_delete_many_by_pattern(full_pattern)
            elapsed = time.time() - start_time
            # 记录基本统计信息
            self._stats['delete_many']['count'] += 1
            self._stats['delete_many']['total_time'] += elapsed
            self._stats['delete_many']['items'] += deleted_count
            return deleted_count
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"通过模式删除多个缓存失败: {full_pattern}, 错误: {str(e)}")
            # 记录错误统计
            self._stats['delete_many']['count'] += 1
            self._stats['delete_many']['total_time'] += elapsed
            self.add_error(strategy_type='base', operation='delete_pattern')
            return 0


class VersionedCache:
    """版本化缓存管理类，适用于不支持delete_pattern的缓存后端
    
    通过版本号机制使缓存失效，避免直接依赖delete_pattern方法
    
    特性:
    - 支持缓存统计记录（命中、未命中、耗时、错误等）
    - 提供异常处理和容错机制
    - 按策略类型分类统计信息
    """
    
    def __init__(self, prefix: str = "", default_timeout: int = 3600):
        """初始化版本化缓存管理器
        
        Args:
            prefix: 缓存键前缀
            default_timeout: 默认缓存超时时间（秒）
        """
        self.prefix = prefix
        self.default_timeout = default_timeout
        self.version_key = f"{prefix}_version" if prefix else "cache_version"
        
        # 初始化统计信息
        self._stats = {
            'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
            'set': {'count': 0, 'total_time': 0.0},
            'increment_version': {'count': 0, 'total_time': 0.0},
            'errors': {'get': 0, 'set': 0, 'increment_version': 0}
        }
        self._strategy_stats = {}
        self._strategy_type = 'versioned'
    
    def get_version(self) -> int:
        """获取当前缓存版本号
        
        Returns:
            int: 当前版本号
        """
        try:
            return cache.get(self.version_key, 0)
        except Exception as e:
            logger.error(f"获取缓存版本号失败: {str(e)}")
            return 0
    
    def add_get(self, hit: bool = False, elapsed: float = 0.0) -> None:
        """记录获取缓存操作的统计信息
        
        Args:
            hit: 是否命中缓存
            elapsed: 操作耗时（秒）
        """
        # 更新总体统计
        self._stats['get']['count'] += 1
        if hit:
            self._stats['get']['hits'] += 1
        else:
            self._stats['get']['misses'] += 1
        self._stats['get']['total_time'] += elapsed
        
        # 更新策略类型统计
        if self._strategy_type not in self._strategy_stats:
            self._strategy_stats[self._strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'increment_version': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'increment_version': 0}
            }
        
        self._strategy_stats[self._strategy_type]['get']['count'] += 1
        if hit:
            self._strategy_stats[self._strategy_type]['get']['hits'] += 1
        else:
            self._strategy_stats[self._strategy_type]['get']['misses'] += 1
        self._strategy_stats[self._strategy_type]['get']['total_time'] += elapsed
    
    def add_set(self, elapsed: float = 0.0) -> None:
        """记录设置缓存操作的统计信息
        
        Args:
            elapsed: 操作耗时（秒）
        """
        # 更新总体统计
        self._stats['set']['count'] += 1
        self._stats['set']['total_time'] += elapsed
        
        # 更新策略类型统计
        if self._strategy_type not in self._strategy_stats:
            self._strategy_stats[self._strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'increment_version': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'increment_version': 0}
            }
        
        self._strategy_stats[self._strategy_type]['set']['count'] += 1
        self._strategy_stats[self._strategy_type]['set']['total_time'] += elapsed
    
    def add_increment_version(self, elapsed: float = 0.0) -> None:
        """记录增加版本号操作的统计信息
        
        Args:
            elapsed: 操作耗时（秒）
        """
        # 更新总体统计
        self._stats['increment_version']['count'] += 1
        self._stats['increment_version']['total_time'] += elapsed
        
        # 更新策略类型统计
        if self._strategy_type not in self._strategy_stats:
            self._strategy_stats[self._strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'increment_version': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'increment_version': 0}
            }
        
        self._strategy_stats[self._strategy_type]['increment_version']['count'] += 1
        self._strategy_stats[self._strategy_type]['increment_version']['total_time'] += elapsed
    
    def add_error(self, operation: str = 'get') -> None:
        """记录缓存操作的错误信息
        
        Args:
            operation: 操作类型（get/set/increment_version）
        """
        # 更新总体统计
        if operation in self._stats['errors']:
            self._stats['errors'][operation] += 1
        
        # 更新策略类型统计
        if self._strategy_type not in self._strategy_stats:
            self._strategy_stats[self._strategy_type] = {
                'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
                'set': {'count': 0, 'total_time': 0.0},
                'increment_version': {'count': 0, 'total_time': 0.0},
                'errors': {'get': 0, 'set': 0, 'increment_version': 0}
            }
        
        if operation in self._strategy_stats[self._strategy_type]['errors']:
            self._strategy_stats[self._strategy_type]['errors'][operation] += 1
    
    def get_stats(self) -> dict:
        """获取缓存统计信息
        
        Returns:
            dict: 统计信息字典
        """
        return {
            'summary': self._stats,
            'by_strategy': self._strategy_stats
        }
    
    def reset_stats(self) -> None:
        """重置缓存统计信息"""
        self._stats = {
            'get': {'hits': 0, 'misses': 0, 'total_time': 0.0},
            'set': {'count': 0, 'total_time': 0.0},
            'increment_version': {'count': 0, 'total_time': 0.0},
            'errors': {'get': 0, 'set': 0, 'increment_version': 0}
        }
        self._strategy_stats = {}
    
    def increment_version(self) -> int:
        """增加缓存版本号，使相关缓存失效，记录统计信息
        
        Returns:
            int: 新的版本号
        """
        start_time = time.time()
        try:
            new_version = self.get_version() + 1
            cache.set(self.version_key, new_version, self.default_timeout)
            elapsed = time.time() - start_time
            # 记录基本统计信息
            self.add_increment_version(elapsed=elapsed)
            return new_version
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"增加缓存版本号失败: {str(e)}")
            # 记录错误统计
            self.add_error(operation='increment_version')
            # 返回当前版本号作为降级策略
            return self.get_version()
    
    def get_key(self, key: str, **kwargs) -> str:
        """生成带版本号的完整缓存键
        
        Args:
            key: 基础缓存键
            **kwargs: 额外参数，用于格式化缓存键
        
        Returns:
            str: 完整的缓存键
        """
        version = self.get_version()
        base_key = f"{self.prefix}_{key}_{version}" if self.prefix else f"{key}_{version}"
        if kwargs:
            return base_key.format(**kwargs)
        return base_key
    
    def get(self, key: str, default: Any = None, **kwargs) -> Any:
        """获取缓存值，记录统计信息
        
        Args:
            key: 缓存键
            default: 默认值
            **kwargs: 用于格式化缓存键的参数
        
        Returns:
            Any: 缓存值或默认值
        """
        cache_key = self.get_key(key, **kwargs)
        start_time = time.time()
        try:
            value = cache.get(cache_key, default)
            elapsed = time.time() - start_time
            # 记录基本统计信息
            self.add_get(hit=(value is not None), elapsed=elapsed)
            return value
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"获取版本化缓存失败: {cache_key}, 错误: {str(e)}")
            # 记录错误统计
            self.add_error(operation='get')
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None, **kwargs) -> None:
        """设置缓存值，记录统计信息
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 超时时间（秒），None表示使用默认值
            **kwargs: 用于格式化缓存键的参数
        """
        cache_key = self.get_key(key, **kwargs)
        actual_timeout = timeout if timeout is not None else self.default_timeout
        start_time = time.time()
        try:
            cache.set(cache_key, value, actual_timeout)
            elapsed = time.time() - start_time
            # 记录基本统计信息
            self.add_set(elapsed=elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"设置版本化缓存失败: {cache_key}, 错误: {str(e)}")
            # 记录错误统计
            self.add_error(operation='set')
    
    def clear_cache(self) -> int:
        """清除所有相关缓存，记录统计信息
        
        Returns:
            int: 新的版本号
        """
        return self.increment_version()


# 全局缓存管理器实例
default_cache_manager = CacheManager()

# 装饰器缓存统计信息
decorator_cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_time': 0.0,
    'errors': 0,
    'functions': {}
}

def get_decorator_cache_stats() -> dict:
    """获取装饰器缓存统计信息
    
    Returns:
        dict: 统计信息字典
    """
    return decorator_cache_stats.copy()

def reset_decorator_cache_stats() -> None:
    """重置装饰器缓存统计信息"""
    global decorator_cache_stats
    decorator_cache_stats = {
        'hits': 0,
        'misses': 0,
        'total_time': 0.0,
        'errors': 0,
        'functions': {}
    }

def cached(timeout: int = 3600, key_prefix: str = ""):
    """缓存函数结果的装饰器，支持统计功能
    
    Args:
        timeout: 缓存超时时间（秒）
        key_prefix: 缓存键前缀
    
    Returns:
        Callable: 装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        # 初始化函数级别的统计信息
        func_name = func.__name__
        module_name = func.__module__
        full_func_name = f"{module_name}.{func_name}"
        
        if full_func_name not in decorator_cache_stats['functions']:
            decorator_cache_stats['functions'][full_func_name] = {
                'hits': 0,
                'misses': 0,
                'total_time': 0.0,
                'errors': 0,
                'timeout': timeout,
                'key_prefix': key_prefix
            }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # 生成缓存键
                # 将参数转换为可哈希的形式
                key_parts = [func_name]
                
                # 处理位置参数
                for arg in args:
                    try:
                        # 尝试将参数转换为字符串
                        key_parts.append(str(arg))
                    except:
                        # 如果无法转换，使用其类型名称
                        key_parts.append(type(arg).__name__)
                
                # 处理关键字参数（排序以确保一致性）
                for k, v in sorted(kwargs.items()):
                    try:
                        key_parts.append(f"{k}={v}")
                    except:
                        key_parts.append(f"{k}={type(v).__name__}")
                
                # 生成最终的缓存键
                cache_key = f"{key_prefix}_cached_{'_'.join(key_parts)}" if key_prefix else f"cached_{'_'.join(key_parts)}"
                
                # 尝试从缓存获取结果
                result = cache.get(cache_key)
                elapsed = time.time() - start_time
                
                if result is not None:
                    # 记录缓存命中
                    decorator_cache_stats['hits'] += 1
                    decorator_cache_stats['total_time'] += elapsed
                    decorator_cache_stats['functions'][full_func_name]['hits'] += 1
                    decorator_cache_stats['functions'][full_func_name]['total_time'] += elapsed
                    return result
                
                # 缓存未命中，调用原始函数
                result = func(*args, **kwargs)
                
                # 缓存结果
                cache.set(cache_key, result, timeout)
                
                # 更新函数执行后的统计信息
                total_elapsed = time.time() - start_time
                decorator_cache_stats['misses'] += 1
                decorator_cache_stats['total_time'] += total_elapsed
                decorator_cache_stats['functions'][full_func_name]['misses'] += 1
                decorator_cache_stats['functions'][full_func_name]['total_time'] += total_elapsed
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"装饰器缓存执行失败: {full_func_name}, 错误: {str(e)}")
                # 记录错误统计
                decorator_cache_stats['errors'] += 1
                decorator_cache_stats['functions'][full_func_name]['errors'] += 1
                # 调用原始函数作为降级策略
                return func(*args, **kwargs)
        return wrapper
    return decorator


def clear_cached_function(key_prefix: str, func_name: str) -> bool:
    """清除指定函数的缓存
    
    Args:
        key_prefix: 缓存键前缀
        func_name: 函数名称
    
    Returns:
        bool: 是否成功清除
    """
    pattern = f"{key_prefix}_cached_{func_name}_*" if key_prefix else f"cached_{func_name}_*"
    return safe_delete_pattern(pattern)


def get_cache_stats(include_decorator_stats: bool = True, include_default_manager: bool = True) -> dict:
    """获取完整的缓存统计信息，包括所有缓存策略
    
    Args:
        include_decorator_stats: 是否包含装饰器缓存统计
        include_default_manager: 是否包含默认缓存管理器统计
    
    Returns:
        dict: 缓存统计数据
    """
    stats = {
        "backend": cache.__class__.__name__,
        "has_delete_pattern": hasattr(cache, "delete_pattern"),
        "has_keys": hasattr(cache, "keys"),
        "timestamp": int(time.time())
    }
    
    # 尝试获取更详细的统计信息（如果缓存后端支持）
    if hasattr(cache, "_cache") and hasattr(cache._cache, "stats"):
        try:
            cache_stats = cache._cache.stats()
            if isinstance(cache_stats, dict):
                stats.update(cache_stats)
        except:
            pass
    
    # 添加装饰器缓存统计
    if include_decorator_stats:
        try:
            stats["decorator_cache"] = get_decorator_cache_stats()
        except:
            stats["decorator_cache"] = {"error": "Failed to get decorator cache stats"}
    
    # 添加默认缓存管理器统计
    if include_default_manager:
        try:
            stats["default_manager"] = default_cache_manager.get_stats()
        except:
            stats["default_manager"] = {"error": "Failed to get default manager stats"}
    
    return stats