import logging
import time
import json
import hashlib
from typing import Dict, Any, Optional, Union, Callable, Protocol
from django.conf import settings
from django.utils.functional import wraps
from django.core.cache import cache
from rest_framework.response import Response
from ..utils.cache_utils import CacheManager, VersionedCache, safe_delete_pattern, safe_delete_many_by_pattern

logger = logging.getLogger(__name__)


# 定义缓存策略接口
class CacheStrategy(Protocol):
    """缓存策略接口，定义缓存操作的标准行为"""
    
    def get_key(self, key_pattern: str, **kwargs) -> str:
        """生成缓存键"""
        ...
        
    def get_cached_data(self, cache_key: str) -> object:
        """从缓存获取数据"""
        ...
        
    def set_cached_data(self, cache_key: str, data: object, timeout: int = None) -> None:
        """设置缓存数据"""
        ...
        
    def delete_cached_data(self, cache_key: str) -> None:
        """删除特定缓存键的数据"""
        ...
        
    def clear_pattern_caches(self, pattern: str) -> None:
        """清除匹配特定模式的所有缓存"""
        ...
        
    def invalidate_cache_on_update(self) -> None:
        """在更新操作后使相关缓存失效"""
        ...
        
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        ...


class BaseCacheStrategy:
    """基础缓存策略实现"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.model_name = None
        # 缓存统计信息
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._errors = 0
        self._total_time = 0
        self._operation_count = 0
    
    def set_model_name(self, model_name: str) -> None:
        """设置模型名称"""
        self.model_name = model_name
    
    def get_key(self, key_pattern: str, **kwargs) -> str:
        return self.cache_manager.get_key(key_pattern, **kwargs)
    
    def get_cached_data(self, cache_key: str) -> object:
        start_time = time.time()
        try:
            data = self.cache_manager.get(cache_key)
            if data is not None:
                self._hits += 1
            else:
                self._misses += 1
            return data
        except Exception as e:
            logger.error(f"获取缓存数据失败: {cache_key}, 错误: {str(e)}")
            self._misses += 1
            self._errors += 1
            return None
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def set_cached_data(self, cache_key: str, data: object, timeout: int = None) -> None:
        start_time = time.time()
        try:
            self.cache_manager.set(cache_key, data, timeout)
            self._sets += 1
        except Exception as e:
            logger.error('设置缓存数据失败: %s, 错误: %s', cache_key, str(e))
            self._errors += 1
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def delete_cached_data(self, cache_key: str) -> None:
        start_time = time.time()
        try:
            self.cache_manager.delete(cache_key)
            self._deletes += 1
        except Exception as e:
            logger.error('删除缓存数据失败: %s, 错误: %s', cache_key, str(e))
            self._errors += 1
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def clear_pattern_caches(self, pattern: str) -> None:
        start_time = time.time()
        try:
            success = self.cache_manager.safe_delete_pattern(pattern)
            if not success:
                logger.debug('缓存模式删除失败，使用备用方案清除: %s', pattern)
                self._fallback_clear_cache()
            else:
                self._deletes += 1
        except Exception as e:
            logger.error('清除缓存模式时发生异常: %s, 错误: %s', pattern, str(e))
            self._errors += 1
            self._fallback_clear_cache()
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def _fallback_clear_cache(self) -> None:
        """清除缓存的备用方案"""
        try:
            cache.clear()
            logger.debug('已清除所有缓存')
        except Exception as e:
            logger.error('清除缓存失败: %s', str(e))
    
    def invalidate_cache_on_update(self) -> None:
        """基本的缓存失效策略"""
        start_time = time.time()
        try:
            if self.model_name:
                # 清除所有查询集缓存
                self.clear_pattern_caches('queryset_*')
                # 清除所有列表和详情缓存
                self.clear_pattern_caches('list_*')
                self.clear_pattern_caches('retrieve_*')
                # 如果是树结构数据，也清除树缓存
                self.clear_pattern_caches('tree')
                # 记录缓存清理日志
                logger.debug('已清除%s相关的缓存', self.model_name)
        except Exception as e:
            logger.error('清除%s缓存时发生异常: %s', self.model_name, str(e))
            self._errors += 1
            self._fallback_clear_cache()
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        total_ops = self._hits + self._misses
        hit_rate = (self._hits / total_ops) * 100 if total_ops > 0 else 0
        avg_time = self._total_time / self._operation_count if self._operation_count > 0 else 0
        
        return {
            'strategy': 'base',
            'model': self.model_name,
            'hits': self._hits,
            'misses': self._misses,
            'sets': self._sets,
            'deletes': self._deletes,
            'errors': self._errors,
            'hit_rate': round(hit_rate, 2),
            'total_operations': total_ops,
            'operation_count': self._operation_count,
            'total_time': round(self._total_time, 4),
            'avg_time_per_operation': round(avg_time, 6)
        }
    
    def reset_stats(self) -> None:
        """重置缓存统计信息"""
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._errors = 0
        self._total_time = 0
        self._operation_count = 0


class VersionedCacheStrategy(BaseCacheStrategy):
    """版本化缓存策略实现"""
    
    def __init__(self, cache_manager: CacheManager):
        super().__init__(cache_manager)
        self.version_key = f"{cache_manager.prefix}_version" if cache_manager.prefix else "default_version"
        # 确保版本号存在
        try:
            if self.cache_manager.get(self.version_key) is None:
                self.cache_manager.set(self.version_key, 1)
        except Exception as e:
            logger.error('初始化版本号失败: %s', str(e))
            # 设置默认版本号作为后备方案
            self._current_version = 1
        # 版本变更计数器
        self._version_changes = 0
    
    def _get_version(self) -> int:
        """获取当前版本号"""
        start_time = time.time()
        try:
            version = self.cache_manager.get(self.version_key)
            return version if version is not None else 1
        except Exception as e:
            logger.error('获取版本号失败: %s', str(e))
            self._errors += 1
            return 1
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def _increment_version(self) -> int:
        """增加版本号"""
        start_time = time.time()
        try:
            version = self._get_version() + 1
            self.cache_manager.set(self.version_key, version)
            self._version_changes += 1
            self._sets += 1
            return version
        except Exception as e:
            logger.error('增加版本号失败: %s', str(e))
            self._errors += 1
            return self._get_version() + 1
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def get_cached_data(self, cache_key: str) -> object:
        try:
            # 添加版本号到缓存键
            versioned_key = f"{cache_key}_v{self._get_version()}"
            data = self.cache_manager.get(versioned_key)
            if data is not None:
                self._hits += 1
            else:
                self._misses += 1
            return data
        except Exception as e:
            logger.error('获取带版本号的缓存失败: %s', str(e))
            self._misses += 1
            self._errors += 1
            return None
    
    def set_cached_data(self, cache_key: str, data: object, timeout: int = None) -> None:
        try:
            # 添加版本号到缓存键
            versioned_key = f"{cache_key}_v{self._get_version()}"
            self.cache_manager.set(versioned_key, data, timeout)
            self._sets += 1
        except Exception as e:
            logger.error('设置带版本号的缓存失败: %s', str(e))
            self._errors += 1
    
    def invalidate_cache_on_update(self) -> None:
        """通过增加版本号使所有缓存失效"""
        try:
            new_version = self._increment_version()
            if self.model_name:
                logger.debug('已更新%s缓存版本至%s', self.model_name, new_version)
        except Exception as e:
            logger.error('更新缓存版本失败: %s', str(e))
            self._errors += 1
            # 降级到基础策略
            super().invalidate_cache_on_update()
    
    def get_stats(self) -> dict:
        """获取版本化缓存统计信息"""
        base_stats = super().get_stats()
        avg_time = self._total_time / self._operation_count if self._operation_count > 0 else 0
        
        base_stats.update({
            'strategy': 'versioned',
            'current_version': self._get_version(),
            'version_changes': self._version_changes,
            'errors': self._errors,
            'operation_count': self._operation_count,
            'total_time': round(self._total_time, 4),
            'avg_time_per_operation': round(avg_time, 6)
        })
        return base_stats
    
    def reset_stats(self) -> None:
        """重置版本化缓存统计信息"""
        super().reset_stats()
        self._version_changes = 0


class TTLCacheStrategy(BaseCacheStrategy):
    """基于TTL(Time-To-Live)的缓存策略实现
    
    为不同类型的数据设置不同的缓存过期时间
    """
    
    def __init__(self, cache_manager: CacheManager):
        super().__init__(cache_manager)
        # 默认TTL设置
        self.default_ttl_settings = {
            'queryset': 600,  # 查询集缓存10分钟
            'list': 600,      # 列表数据缓存10分钟
            'retrieve': 1800, # 详情数据缓存30分钟
            'tree': 1200,     # 树结构数据缓存20分钟
            'statistics': 300 # 统计数据缓存5分钟
        }
        # 自定义TTL设置
        self.custom_ttl = {}
    
    def set_ttl(self, cache_type: str, timeout: int) -> None:
        """设置特定类型缓存的TTL
        
        Args:
            cache_type: 缓存类型
            timeout: 过期时间（秒）
        """
        self.custom_ttl[cache_type] = timeout
    
    def get_ttl(self, cache_type: str) -> int:
        """获取特定类型缓存的TTL
        
        Args:
            cache_type: 缓存类型
        
        Returns:
            int: 过期时间（秒）
        """
        return self.custom_ttl.get(cache_type, self.default_ttl_settings.get(cache_type, self.default_ttl_settings['queryset']))
    
    def set_cached_data(self, cache_key: str, data: object, timeout: int = None) -> None:
        # 如果未指定timeout，根据缓存键类型选择合适的TTL
        if timeout is None:
            for cache_type, ttl in self.default_ttl_settings.items():
                if cache_type in cache_key:
                    timeout = self.custom_ttl.get(cache_type, ttl)
                    break
            else:
                timeout = self.default_ttl_settings['queryset']
        
        self.cache_manager.set(cache_key, data, timeout)
        self._sets += 1
        logger.debug(f"设置TTL缓存: {cache_key}, 过期时间: {timeout}秒")
    
    def invalidate_cache_on_update(self) -> None:
        """基于TTL的缓存失效策略
        
        优先清除最影响用户体验的缓存（如树结构和详情页）
        对于列表和查询集缓存，依赖TTL自动过期
        """
        if self.model_name:
            try:
                # 首先清除详情和树结构缓存（影响用户体验最直接）
                self.clear_pattern_caches('retrieve_*')
                self.clear_pattern_caches('tree')
                # 记录缓存清理日志
                logger.debug('已清除%s的详情和树结构缓存', self.model_name)
                # 列表和查询集缓存依赖TTL自动过期，减少缓存清理开销
            except Exception as e:
                logger.error('清除%s缓存时发生异常: %s', self.model_name, str(e))
                self._errors += 1
                self._fallback_clear_cache()
    
    def get_stats(self) -> dict:
        """获取TTL缓存统计信息"""
        base_stats = super().get_stats()
        total_ops = self._hits + self._misses
        hit_rate = (self._hits / total_ops) * 100 if total_ops > 0 else 0
        avg_time = self._total_time / self._operation_count if self._operation_count > 0 else 0
        
        base_stats.update({
            'strategy': 'ttl',
            'ttl_settings': self.default_ttl_settings,
            'custom_ttl': self.custom_ttl,
            'errors': self._errors,
            'operation_count': self._operation_count,
            'total_time': round(self._total_time, 4),
            'avg_time_per_operation': round(avg_time, 6)
        })
        return base_stats


class SelectiveCacheStrategy(BaseCacheStrategy):
    """选择性缓存策略实现
    
    只缓存频繁访问但不经常更新的数据
    """
    
    def __init__(self, cache_manager: CacheManager):
        super().__init__(cache_manager)
        # 定义需要缓存的操作类型
        self.cacheable_actions = {'list', 'retrieve', 'tree', 'statistics'}
        # 定义不需要缓存的参数模式
        self.non_cacheable_params = {'no_cache': 'true', 'refresh': 'true'}
        # 已标记为不需要缓存的键
        self._non_cacheable_keys = set()
    
    def should_cache(self, action: str, params: dict = None) -> bool:
        """判断是否应该缓存
        
        Args:
            action: 操作类型
            params: 请求参数
        
        Returns:
            bool: 是否应该缓存
        """
        # 检查操作类型是否可缓存
        if action not in self.cacheable_actions:
            return False
        
        # 检查是否包含不允许缓存的参数
        if params:
            for param, value in self.non_cacheable_params.items():
                if params.get(param) == value:
                    return False
        
        return True
    
    def get_cached_data(self, cache_key: str) -> object:
        start_time = time.time()
        try:
            # 检查是否在不缓存列表中
            if cache_key in self._non_cacheable_keys:
                self._misses += 1
                return None
            
            return super().get_cached_data(cache_key)
        except Exception as e:
            logger.error('获取缓存数据失败: %s', str(e))
            self._errors += 1
            return None
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def set_cached_data(self, cache_key: str, data: object, timeout: int = None) -> None:
        start_time = time.time()
        try:
            # 只缓存不包含敏感数据的响应
            if isinstance(data, dict) and ('error' not in data or data['error'] is None):
                super().set_cached_data(cache_key, data, timeout)
            else:
                # 将错误响应添加到不缓存列表
                self._non_cacheable_keys.add(cache_key)
        except Exception as e:
            logger.error('设置缓存数据失败: %s', str(e))
            self._errors += 1
        finally:
            self._total_time += time.time() - start_time
            self._operation_count += 1
    
    def invalidate_cache_on_update(self) -> None:
        """选择性缓存失效策略
        
        只清除特定操作的缓存，避免过度清理
        """
        if self.model_name:
            try:
                # 只清除可缓存操作的缓存
                for action in self.cacheable_actions:
                    self.clear_pattern_caches('%s_*' % action)
                # 清空不缓存列表
                self._non_cacheable_keys.clear()
                # 记录缓存清理日志
                logger.debug('已清除%s的可缓存操作缓存', self.model_name)
            except Exception as e:
                logger.error('清除%s缓存时发生异常: %s', self.model_name, str(e))
                self._errors += 1
                self._fallback_clear_cache()
    
    def get_stats(self) -> dict:
        """获取选择性缓存统计信息"""
        base_stats = super().get_stats()
        avg_time = self._total_time / self._operation_count if self._operation_count > 0 else 0
        
        base_stats.update({
            'strategy': 'selective',
            'cacheable_actions': list(self.cacheable_actions),
            'non_cacheable_count': len(self._non_cacheable_keys),
            'errors': self._errors,
            'operation_count': self._operation_count,
            'total_time': round(self._total_time, 4),
            'avg_time_per_operation': round(avg_time, 6)
        })
        return base_stats
    
    def reset_stats(self) -> None:
        """重置选择性缓存统计信息"""
        super().reset_stats()
        self._non_cacheable_keys.clear()


class CacheStrategySelector:
    """缓存策略选择器，根据不同场景自动选择合适的缓存策略"""
    
    @staticmethod
    def get_strategy(cache_manager: CacheManager, viewset_type: str = None, data_type: str = None) -> CacheStrategy:
        """根据视图集类型和数据类型选择合适的缓存策略
        
        Args:
            cache_manager: 缓存管理器实例
            viewset_type: 视图集类型（如 'readonly', 'model', 'custom'）
            data_type: 数据类型（如 'tree', 'list', 'detail', 'statistics'）
        
        Returns:
            CacheStrategy: 选择的缓存策略
        """
        # 策略选择逻辑
        if viewset_type == 'readonly' and data_type == 'tree':
            # 对于只读的树结构数据，使用TTL策略
            strategy = TTLCacheStrategy(cache_manager)
            strategy.set_ttl('tree', 3600)  # 树结构数据缓存1小时
            return strategy
        elif viewset_type == 'model' and data_type == 'statistics':
            # 对于统计数据，使用选择性缓存策略
            return SelectiveCacheStrategy(cache_manager)
        elif viewset_type == 'custom' or data_type == 'frequent_update':
            # 对于频繁更新的数据，使用版本化策略
            return VersionedCacheStrategy(cache_manager)
        else:
            # 默认使用基础策略
            return BaseCacheStrategy(cache_manager)


class CachedViewMixin:
    """缓存视图混入类，提供统一的缓存管理功能
    
    此混入类集成了CacheManager，为视图提供统一的缓存获取、设置和清除功能
    特别针对不同缓存后端进行了兼容性处理，简化了缓存操作代码
    
    特点：
    1. 统一的缓存键生成规则
    2. 支持多种缓存策略（普通缓存、版本化缓存、TTL缓存、选择性缓存）
    3. 通过装饰器方式添加缓存，不影响业务代码
    4. 支持自定义缓存超时时间和缓存键前缀
    5. 自动为ReadOnlyModelViewSet添加常见方法的缓存
    6. 内置缓存统计功能，支持性能监控
    7. 自动根据视图类型和数据类型选择合适的缓存策略
    """
    
    # 默认缓存过期时间（秒）
    DEFAULT_CACHE_TIMEOUT = 600  # 10分钟
    
    # 缓存管理器实例
    cache_manager = None
    
    # 缓存键前缀，默认会根据视图集类名或模型名生成
    CACHE_KEY_PREFIX = None
    
    # 缓存策略类型，默认为None（使用基础策略）
    CACHE_STRATEGY_TYPE = None  # 可选值: None, 'versioned', 'ttl', 'selective'
    
    # 视图集类型，用于自动选择缓存策略
    VIEWSET_TYPE = None  # 可选值: 'readonly', 'model', 'custom'
    
    # 数据类型，用于自动选择缓存策略
    DATA_TYPE = None  # 可选值: 'tree', 'list', 'detail', 'statistics', 'frequent_update'
    
    # 缓存策略实例
    _cache_strategy: Optional[CacheStrategy] = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化缓存管理器
        self._initialize_cache_manager()
        # 初始化缓存策略
        self._initialize_cache_strategy()
        # 自动为ReadOnlyModelViewSet添加缓存（如果适用）
        self._auto_setup_cache_for_readonly_views()
        # 初始化性能统计
        self._cache_stats_enabled = getattr(settings, 'CACHE_STATS_ENABLED', False)
    
    def _initialize_cache_manager(self) -> None:
        """初始化缓存管理器"""
        if self.cache_manager is None:
            # 确定缓存前缀
            prefix = self.CACHE_KEY_PREFIX
            if not prefix:
                # 优先从queryset获取模型名作为前缀
                if hasattr(self, 'queryset') and self.queryset:
                    prefix = self.queryset.model.__name__.lower()
                else:
                    # 否则使用视图集类名作为前缀
                    prefix = self.__class__.__name__.lower().replace('viewset', '')
            
            self.cache_manager = CacheManager(prefix=prefix, default_timeout=self.DEFAULT_CACHE_TIMEOUT)
    
    def _initialize_cache_strategy(self) -> None:
        """初始化缓存策略"""
        if self.cache_manager and self._cache_strategy is None:
            # 如果指定了具体的策略类型，使用指定的策略
            if self.CACHE_STRATEGY_TYPE == 'versioned':
                self._cache_strategy = VersionedCacheStrategy(self.cache_manager)
            elif self.CACHE_STRATEGY_TYPE == 'ttl':
                self._cache_strategy = TTLCacheStrategy(self.cache_manager)
            elif self.CACHE_STRATEGY_TYPE == 'selective':
                self._cache_strategy = SelectiveCacheStrategy(self.cache_manager)
            else:
                # 否则使用策略选择器自动选择合适的策略
                self._cache_strategy = CacheStrategySelector.get_strategy(
                    self.cache_manager,
                    viewset_type=self.VIEWSET_TYPE,
                    data_type=self.DATA_TYPE
                )
            
            # 设置模型名称
            if hasattr(self, 'queryset') and self.queryset:
                model_name = self.queryset.model.__name__.lower()
                if hasattr(self._cache_strategy, 'set_model_name'):
                    self._cache_strategy.set_model_name(model_name)
    
    def get_cache_key(self, action: str, **kwargs) -> str:
        """生成统一的缓存键
        
        Args:
            action: 视图集动作名称（如 'list', 'retrieve', 'statistics' 等）
            **kwargs: 用于构建缓存键的额外参数
            
        Returns:
            str: 生成的缓存键
        """
        # 基本键模式
        key_pattern = f"{action}_"
        
        # 添加参数到缓存键
        if kwargs:
            # 对复杂参数进行序列化处理，确保缓存键的唯一性
            key_parts = []
            for k, v in sorted(kwargs.items()):
                # 对字典、列表等复杂类型进行JSON序列化
                if isinstance(v, (dict, list, tuple)):
                    try:
                        value_str = json.dumps(v, sort_keys=True)[:200]  # 限制长度，避免键过长
                        key_parts.append(f"{k}={hashlib.md5(value_str.encode()).hexdigest()[:8]}")
                    except Exception:
                        key_parts.append(f"{k}=complex")
                else:
                    # 对简单类型直接使用
                    key_parts.append(f"{k}={str(v)[:100]}")
            key_pattern += "_".join(key_parts)
        
        if self._cache_strategy:
            return self._cache_strategy.get_key(key_pattern)
        return self.cache_manager.get_key(key_pattern)
    
    def _get_cached_data(self, cache_key: str) -> object:
        """从缓存获取数据
        
        Args:
            cache_key: 缓存键
        
        Returns:
            object: 缓存的数据，如果不存在则返回None
        """
        # 只有GET请求才使用缓存
        if hasattr(self, 'request') and self.request.method == 'GET':
            start_time = time.time() if self._cache_stats_enabled else 0
            try:
                if self._cache_strategy:
                    data = self._cache_strategy.get_cached_data(cache_key)
                else:
                    data = self.cache_manager.get(cache_key)
                
                # 记录缓存统计信息
                if self._cache_stats_enabled:
                    elapsed = time.time() - start_time
                    strategy_type = self.CACHE_STRATEGY_TYPE or 'base'
                    if data is not None:
                        self.cache_manager.add_hit(strategy_type, elapsed)
                    else:
                        self.cache_manager.add_miss(strategy_type, elapsed)
                
                return data
            except Exception as e:
                logger.error(f"获取缓存数据失败: {cache_key}, 错误: {str(e)}")
                # 缓存获取失败时，返回None，允许从原始数据源获取
                return None
        return None
    
    def _set_cached_data(self, cache_key: str, data: object, timeout: int = None) -> None:
        """设置缓存数据
        
        Args:
            cache_key: 缓存键
            data: 要缓存的数据
            timeout: 缓存过期时间（秒），默认为None（使用默认超时）
        """
        # 只有GET请求才设置缓存
        if hasattr(self, 'request') and self.request.method == 'GET':
            start_time = time.time() if self._cache_stats_enabled else 0
            try:
                # 避免缓存无法序列化的数据
                if data is not None:
                    # 尝试序列化数据，确保可以被缓存
                    try:
                        json.dumps(data, cls=DjangoJSONEncoder)
                    except (TypeError, OverflowError) as e:
                        logger.warning(f"数据无法序列化，不进行缓存: {str(e)}")
                        return
                    
                    if self._cache_strategy:
                        self._cache_strategy.set_cached_data(cache_key, data, timeout)
                    else:
                        self.cache_manager.set(cache_key, data, timeout)
                        
                    # 记录缓存统计信息
                    if self._cache_stats_enabled:
                        elapsed = time.time() - start_time
                        strategy_type = self.CACHE_STRATEGY_TYPE or 'base'
                        self.cache_manager.add_set(strategy_type, elapsed)
            except Exception as e:
                logger.error(f"设置缓存数据失败: {cache_key}, 错误: {str(e)}")
    
    def _delete_cached_data(self, cache_key: str) -> None:
        """删除特定缓存键的数据
        
        Args:
            cache_key: 要删除的缓存键
        """
        start_time = time.time() if self._cache_stats_enabled else 0
        try:
            if self._cache_strategy:
                self._cache_strategy.delete_cached_data(cache_key)
            else:
                self.cache_manager.delete(cache_key)
            
            # 记录缓存统计信息
            if self._cache_stats_enabled:
                elapsed = time.time() - start_time
                strategy_type = self.CACHE_STRATEGY_TYPE or 'base'
                self.cache_manager.add_delete(strategy_type, elapsed)
        except Exception as e:
            logger.error(f"删除缓存数据失败: {cache_key}, 错误: {str(e)}")
    
    def cache_response(self, timeout: Optional[int] = None, key_params_func=None, skip_cache_if=None):
        """缓存响应的装饰器
        
        Args:
            timeout: 缓存过期时间（秒），None表示使用默认值
            key_params_func: 生成缓存键参数的函数，接收request作为参数
            skip_cache_if: 跳过缓存的条件函数，接收request和响应数据作为参数
        
        Returns:
            Callable: 装饰后的视图方法
        """
        def decorator(view_method):
            @wraps(view_method)
            def wrapper(self, request, *args, **kwargs):
                # 只对GET请求使用缓存
                if request.method != 'GET':
                    return view_method(self, request, *args, **kwargs)
                
                # 获取动作名称
                action = view_method.__name__
                
                try:
                    # 生成缓存键参数
                    cache_kwargs = {}
                    if key_params_func:
                        try:
                            cache_kwargs = key_params_func(request, *args, **kwargs)
                        except Exception as e:
                            logger.error(f"生成缓存键参数失败: {str(e)}")
                    else:
                        # 默认包含查询参数和分页参数，对复杂参数进行处理
                        if request.GET:
                            # 过滤敏感参数，避免将其包含在缓存键中
                            for param, value in request.GET.dict().items():
                                if not self._is_sensitive_parameter(param):
                                    cache_kwargs[param] = value
                        
                        # 如果有lookup_field参数，也添加到缓存键
                        lookup_field = getattr(self, 'lookup_field', None)
                        if lookup_field and lookup_field in kwargs:
                            cache_kwargs[lookup_field] = kwargs[lookup_field]
                    
                    # 生成缓存键
                    cache_key = self.get_cache_key(action, **cache_kwargs)
                    
                    # 尝试从缓存获取数据
                    cached_data = self._get_cached_data(cache_key)
                    if cached_data is not None:
                        logger.debug(f"缓存命中: {cache_key}")
                        # 检查是否需要跳过缓存（即使命中）
                        if skip_cache_if and callable(skip_cache_if) and skip_cache_if(request, cached_data):
                            logger.debug(f"跳过缓存命中: {cache_key}")
                        else:
                            # 如果缓存的是数据而不是响应对象，需要创建新的响应对象
                            return Response(cached_data)
                    
                    # 调用原始视图方法
                    response = view_method(self, request, *args, **kwargs)
                    
                    # 缓存响应数据
                    if response.status_code == 200:
                        # 检查是否需要跳过缓存
                        if skip_cache_if and callable(skip_cache_if) and skip_cache_if(request, response.data):
                            logger.debug(f"跳过缓存设置: {cache_key}")
                        else:
                            # 只缓存响应的数据部分，而不是整个响应对象，避免序列化问题
                            self._set_cached_data(cache_key, response.data, timeout)
                            logger.debug(f"已缓存响应数据: {cache_key}")
                    
                    return response
                except Exception as e:
                    logger.error(f"缓存处理过程中发生异常: {str(e)}")
                    # 发生异常时，直接调用原始视图方法，不使用缓存
                    return view_method(self, request, *args, **kwargs)
            return wrapper
        return decorator
    
    def _is_sensitive_parameter(self, param_name: str) -> bool:
        """检查参数是否为敏感参数
        
        Args:
            param_name: 参数名
        
        Returns:
            bool: 是否为敏感参数
        """
        # 定义敏感参数列表，可以从settings中获取
        sensitive_params = getattr(settings, 'CACHE_SENSITIVE_PARAMETERS', ['password', 'token', 'auth'])
        param_name_lower = param_name.lower()
        
        return any(sensitive in param_name_lower for sensitive in sensitive_params)
    
    def _clear_pattern_caches(self, pattern: str) -> None:
        """清除匹配特定模式的所有缓存
        
        Args:
            pattern: 缓存键模式，例如 'queryset_*'
        """
        start_time = time.time() if self._cache_stats_enabled else 0
        try:
            if self._cache_strategy:
                self._cache_strategy.clear_pattern_caches(pattern)
            else:
                # 尝试使用安全的模式删除方法
                success = self.cache_manager.safe_delete_pattern(pattern)
                if not success:
                    logger.debug(f"缓存模式删除失败，使用备用方案清除: {pattern}")
                    # 降级到只清除当前视图集相关的缓存，而不是所有缓存
                    try:
                        # 只清除当前视图集前缀下的缓存
                        if self.cache_manager and self.cache_manager.prefix:
                            pattern_with_prefix = f"{self.cache_manager.prefix}_{pattern}"
                            self.cache_manager.safe_delete_pattern(pattern_with_prefix)
                            logger.debug(f"已清除{pattern_with_prefix}相关的缓存")
                    except Exception as e:
                        logger.error(f"清除缓存失败: {str(e)}")
            
            # 记录缓存统计信息
            if self._cache_stats_enabled:
                elapsed = time.time() - start_time
                strategy_type = self.CACHE_STRATEGY_TYPE or 'base'
                self.cache_manager.add_pattern_delete(strategy_type, elapsed)
        except Exception as e:
            logger.error(f"清除缓存模式时发生异常: {pattern}, 错误: {str(e)}")
            # 异常情况下，只记录错误，不执行全局清除，避免影响其他功能
            try:
                # 只清除当前视图集前缀下的缓存
                if self.cache_manager and self.cache_manager.prefix:
                    pattern_with_prefix = f"{self.cache_manager.prefix}_{pattern}"
                    self.cache_manager.safe_delete_pattern(pattern_with_prefix)
                    logger.debug(f"已清除{pattern_with_prefix}相关的缓存")
            except Exception as ex:
                logger.error(f"降级清除缓存失败: {str(ex)}")
    
    def _clear_all_caches(self) -> None:
        """清除与当前视图相关的所有缓存
        
        注意：此操作会尝试清除所有以当前视图prefix开头的缓存
        使用时需谨慎，可能会影响到其他共享同一前缀的缓存
        """
        if self.cache_manager and self.cache_manager.prefix:
            try:
                # 使用安全的模式删除方法
                self.cache_manager.safe_delete_pattern('*')
                logger.debug(f"已清除{self.cache_manager.prefix}相关的所有缓存")
            except Exception as e:
                logger.error(f"清除所有缓存失败: {str(e)}")
    
    def _invalidate_cache_on_update(self) -> None:
        """在更新操作后使相关缓存失效

        视图在create、update、destroy等修改数据的操作后调用此方法
        以清除相关缓存，确保后续请求获取最新数据

        子类可以根据需要覆盖此方法，实现更精确的缓存清除逻辑
        """
        start_time = time.time() if self._cache_stats_enabled else 0
        try:
            if self._cache_strategy:
                # 让策略自己处理缓存失效
                self._cache_strategy.invalidate_cache_on_update()
            else:
                # 默认清除所有与模型相关的查询集缓存
                if hasattr(self, 'queryset') and self.queryset:
                    model_name = self.queryset.model.__name__.lower()
                    # 根据数据类型确定需要清除的缓存模式
                    patterns_to_clear = []
                    
                    # 基本数据操作缓存
                    patterns_to_clear.extend(['queryset_*', 'list_*', 'retrieve_*'])
                    
                    # 树结构数据额外清除树缓存
                    if hasattr(self, 'tree'):
                        patterns_to_clear.append('tree')
                    
                    # 自定义额外的缓存模式
                    additional_patterns = getattr(self, 'ADDITIONAL_CACHE_PATTERNS', [])
                    patterns_to_clear.extend(additional_patterns)
                    
                    # 清除所有相关缓存模式
                    for pattern in patterns_to_clear:
                        self._clear_pattern_caches(pattern)
                    
                    # 记录缓存清理日志
                    logger.debug(f"已清除{model_name}相关的缓存")
            
            # 记录缓存统计信息
            if self._cache_stats_enabled:
                elapsed = time.time() - start_time
                strategy_type = self.CACHE_STRATEGY_TYPE or 'base'
                self.cache_manager.add_invalidation(strategy_type, elapsed)
        except Exception as e:
            logger.error(f"缓存失效处理时发生异常: {str(e)}")
            # 异常情况下，只记录错误，不执行全局清除，避免影响其他功能
    
    def _auto_setup_cache_for_readonly_views(self):
        """自动为ReadOnlyModelViewSet添加缓存支持
        
        为list和retrieve方法自动添加缓存逻辑，支持自定义缓存配置
        """
        try:
            # 检查是否有list方法且尚未添加缓存
            if hasattr(self, 'list') and not hasattr(self.list, '_cached'):
                original_list = self.list
                
                @wraps(original_list)
                def cached_list(self, request, *args, **kwargs):
                    try:
                        # 缓存键包含查询参数、排序和分页信息，过滤敏感参数
                        cache_kwargs = {}
                        if request.GET:
                            for param, value in request.GET.dict().items():
                                if not self._is_sensitive_parameter(param):
                                    cache_kwargs[param] = value
                        
                        # 获取自定义的列表缓存超时时间
                        list_timeout = getattr(self, 'LIST_CACHE_TIMEOUT', None)
                        
                        cache_key = self.get_cache_key('list', **cache_kwargs)
                        cached_data = self._get_cached_data(cache_key)
                        if cached_data is not None:
                            logger.debug(f"列表缓存命中: {cache_key}")
                            # 如果缓存的是数据而不是响应对象，需要创建新的响应对象
                            return Response(cached_data)
                        
                        response = original_list(request, *args, **kwargs)
                        
                        if response.status_code == 200:
                            # 只缓存响应的数据部分，而不是整个响应对象，避免序列化问题
                            self._set_cached_data(cache_key, response.data, list_timeout)
                            logger.debug(f"已缓存列表响应数据: {cache_key}")
                        
                        return response
                    except Exception as e:
                        logger.error(f"列表缓存处理异常: {str(e)}")
                        # 发生异常时，直接调用原始视图方法，不使用缓存
                        return original_list(request, *args, **kwargs)
                
                cached_list._cached = True
                self.list = cached_list.__get__(self)
            
            # 检查是否有retrieve方法且尚未添加缓存
            if hasattr(self, 'retrieve') and not hasattr(self.retrieve, '_cached'):
                original_retrieve = self.retrieve
                
                @wraps(original_retrieve)
                def cached_retrieve(self, request, *args, **kwargs):
                    try:
                        # 缓存键包含lookup_field参数
                        lookup_field = getattr(self, 'lookup_field', 'pk')
                        if lookup_field in kwargs:
                            cache_key = self.get_cache_key('retrieve', **{lookup_field: kwargs[lookup_field]})
                            cached_data = self._get_cached_data(cache_key)
                            if cached_data is not None:
                                logger.debug(f"详情缓存命中: {cache_key}")
                                # 如果缓存的是数据而不是响应对象，需要创建新的响应对象
                                return Response(cached_data)
                        
                        response = original_retrieve(request, *args, **kwargs)
                        
                        if response.status_code == 200:
                            lookup_field = getattr(self, 'lookup_field', 'pk')
                            if lookup_field in kwargs:
                                # 获取自定义的详情缓存超时时间
                                retrieve_timeout = getattr(self, 'RETRIEVE_CACHE_TIMEOUT', None)
                                cache_key = self.get_cache_key('retrieve', **{lookup_field: kwargs[lookup_field]})
                                # 只缓存响应的数据部分，而不是整个响应对象，避免序列化问题
                                self._set_cached_data(cache_key, response.data, retrieve_timeout)
                                logger.debug(f"已缓存详情响应数据: {cache_key}")
                        
                        return response
                    except Exception as e:
                        logger.error(f"详情缓存处理异常: {str(e)}")
                        # 发生异常时，直接调用原始视图方法，不使用缓存
                        return original_retrieve(request, *args, **kwargs)
                
                cached_retrieve._cached = True
                self.retrieve = cached_retrieve.__get__(self)
        except Exception as e:
            logger.error(f"自动设置只读视图缓存失败: {str(e)}")
            # 发生异常时，不影响视图正常功能，只是不使用缓存
    
    def invalidate_cache(self, action: str, **kwargs) -> None:
        """使特定动作的缓存失效
        
        Args:
            action: 视图集动作名称
            **kwargs: 用于构建缓存键的额外参数
        """
        cache_key = self.get_cache_key(action, **kwargs)
        self._delete_cached_data(cache_key)
        logger.debug(f"已使缓存失效: {cache_key}")
    
    def invalidate_list_cache(self, **kwargs) -> None:
        """使列表缓存失效"""
        self._clear_pattern_caches('list_*')
    
    def invalidate_retrieve_cache(self, obj_id: Union[str, int]) -> None:
        """使单个对象的详情缓存失效
        
        Args:
            obj_id: 对象ID
        """
        lookup_field = getattr(self, 'lookup_field', 'pk')
        self.invalidate_cache('retrieve', **{lookup_field: obj_id})


class TTLCachedViewMixin(CachedViewMixin):
    """TTL缓存视图混入类，使用基于时间的缓存策略
    
    此混入类在CachedViewMixin的基础上使用TTL（Time-To-Live）策略，
    为缓存数据设置过期时间，适合于数据有自然过期特性的场景
    
    特性:
    - 支持为不同操作设置不同的缓存过期时间
    - 集成缓存统计功能，支持性能监控
    - 增强的异常处理和容错机制
    
    配置参数:
    - DEFAULT_CACHE_TIMEOUT: 默认缓存过期时间（秒）
    - LIST_CACHE_TIMEOUT: 列表操作的缓存过期时间（秒）
    - RETRIEVE_CACHE_TIMEOUT: 详情操作的缓存过期时间（秒）
    """
    
    # 设置缓存策略类型为TTL
    CACHE_STRATEGY_TYPE = 'ttl'
    
    # 默认缓存过期时间设置（可在子类中覆盖）
    DEFAULT_CACHE_TIMEOUT = 3600  # 默认1小时
    LIST_CACHE_TIMEOUT = 1800     # 列表数据默认30分钟
    RETRIEVE_CACHE_TIMEOUT = 3600  # 详情数据默认1小时


class SelectiveCachedViewMixin(CachedViewMixin):
    """选择性缓存视图混入类，使用条件缓存策略
    
    此混入类在CachedViewMixin的基础上使用选择性缓存策略，
    可以根据请求和数据条件决定是否缓存，适合复杂的缓存控制场景
    
    特性:
    - 支持自定义缓存条件判断函数
    - 集成缓存统计功能，支持性能监控
    - 增强的异常处理和容错机制
    
    配置参数:
    - SHOULD_CACHE_PREDICATE: 用于判断是否应该缓存的函数
    - CACHEABLE_STATUS_CODES: 可缓存的HTTP状态码列表
    """
    
    # 设置缓存策略类型为选择性
    CACHE_STRATEGY_TYPE = 'selective'
    
    # 默认配置
    CACHEABLE_STATUS_CODES = [200]
    
    def should_cache_response(self, request, response, *args, **kwargs):
        """判断响应是否应该被缓存
        
        Args:
            request: HTTP请求对象
            response: HTTP响应对象
            *args: 额外位置参数
            **kwargs: 额外关键字参数
            
        Returns:
            bool: 是否应该缓存响应
        """
        # 检查HTTP方法（默认只缓存GET请求）
        if request.method != 'GET':
            return False
        
        # 检查状态码
        if response.status_code not in self.CACHEABLE_STATUS_CODES:
            return False
        
        # 检查是否有自定义缓存条件函数
        if hasattr(self, 'SHOULD_CACHE_PREDICATE') and callable(self.SHOULD_CACHE_PREDICATE):
            return self.SHOULD_CACHE_PREDICATE(request, response, *args, **kwargs)
        
        return True


class VersionedCachedViewMixin(CachedViewMixin):
    """版本化缓存视图混入类，使用版本号策略管理缓存
    
    此混入类在CachedViewMixin的基础上使用版本号策略，
    使得缓存更新更加高效，特别适合需要频繁更新的数据
    
    特性:
    - 基于版本号的缓存键设计，避免直接清除缓存
    - 集成缓存统计功能，支持性能监控
    - 增强的异常处理和容错机制
    - 与ttl和selective等缓存策略兼容
    """
    
    # 设置缓存策略类型为版本化
    CACHE_STRATEGY_TYPE = 'versioned'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化版本号键
        self.version_key = f"{self.cache_manager.prefix}_version" if self.cache_manager.prefix else "default_version"
        # 确保版本号存在
        try:
            if self.cache_manager.get(self.version_key) is None:
                self.cache_manager.set(self.version_key, 1)
        except Exception as e:
            logger.error(f"初始化版本号失败: {str(e)}")
            # 设置默认版本号作为后备方案
            self._current_version = 1
    
    def _get_version(self) -> int:
        """获取当前版本号
        
        Returns:
            int: 当前版本号
        """
        try:
            version = self.cache_manager.get(self.version_key)
            return version if version is not None else 1
        except Exception as e:
            logger.error(f"获取版本号失败: {str(e)}")
            # 异常情况下返回默认版本号
            return 1
    
    def _increment_version(self) -> int:
        """增加版本号
        
        Returns:
            int: 新的版本号
        """
        try:
            version = self._get_version() + 1
            self.cache_manager.set(self.version_key, version)
            return version
        except Exception as e:
            logger.error(f"增加版本号失败: {str(e)}")
            # 异常情况下返回当前版本号+1，但不更新缓存
            return self._get_version() + 1
    
    def _get_cached_data(self, cache_key: str) -> object:
        """带版本号的缓存获取，集成缓存统计功能
        
        Args:
            cache_key: 基础缓存键
        
        Returns:
            object: 缓存的数据，如果不存在则返回None
        """
        if hasattr(self, 'request') and self.request.method == 'GET':
            try:
                start_time = time.time()
                # 添加版本号到缓存键
                versioned_key = f"{cache_key}_v{self._get_version()}"
                data = self.cache_manager.get(versioned_key)
                
                # 记录缓存统计
                if self._cache_stats_enabled:
                    elapsed = time.time() - start_time
                    hit = data is not None
                    self.cache_manager.add_get(strategy_type='versioned', hit=hit, elapsed=elapsed)
                    
                    # 缓存未命中时记录更详细的信息
                    if not hit:
                        logger.debug(f"缓存未命中: {versioned_key}")
                
                return data
            except Exception as e:
                logger.error(f"获取带版本号的缓存失败: {str(e)}")
                # 记录异常统计
                if self._cache_stats_enabled:
                    self.cache_manager.add_error(strategy_type='versioned', operation='get')
        return None
    
    def _set_cached_data(self, cache_key: str, data: object, timeout: int = None) -> None:
        """带版本号的缓存设置，集成缓存统计功能
        
        Args:
            cache_key: 基础缓存键
            data: 要缓存的数据
            timeout: 缓存过期时间（秒），默认为None（使用默认超时）
        """
        if hasattr(self, 'request') and self.request.method == 'GET':
            try:
                # 检查数据是否可序列化
                if data is not None and not isinstance(data, (str, bytes, int, float, bool, type(None))):
                    # 尝试JSON序列化以验证数据
                    try:
                        json.dumps(data)
                    except (TypeError, OverflowError):
                        logger.warning(f"缓存数据无法序列化，跳过缓存设置: {cache_key}")
                        return
                
                start_time = time.time()
                # 添加版本号到缓存键
                versioned_key = f"{cache_key}_v{self._get_version()}"
                self.cache_manager.set(versioned_key, data, timeout)
                
                # 记录缓存统计
                if self._cache_stats_enabled:
                    elapsed = time.time() - start_time
                    self.cache_manager.add_set(strategy_type='versioned', elapsed=elapsed)
                    logger.debug(f"已缓存带版本号的数据: {versioned_key}")
            except Exception as e:
                logger.error(f"设置带版本号的缓存失败: {str(e)}")
                # 记录异常统计
                if self._cache_stats_enabled:
                    self.cache_manager.add_error(strategy_type='versioned', operation='set')
    
    def _invalidate_cache_on_update(self) -> None:
        """通过增加版本号使所有缓存失效
        
        相比直接清除缓存，使用版本号策略可以避免竞争条件
        并更加高效地管理缓存失效
        """
        try:
            start_time = time.time()
            new_version = self._increment_version()
            
            # 记录缓存失效统计
            if self._cache_stats_enabled:
                elapsed = time.time() - start_time
                self.cache_manager.add_invalidation(strategy_type='versioned', elapsed=elapsed)
            
            if hasattr(self, 'queryset') and self.queryset:
                model_name = self.queryset.model.__name__.lower()
                logger.debug(f"已更新{model_name}缓存版本至{new_version}")
        except Exception as e:
            logger.error(f"更新缓存版本失败: {str(e)}")
            # 记录异常统计
            if self._cache_stats_enabled:
                self.cache_manager.add_error(strategy_type='versioned', operation='invalidate')
            # 降级到父类的缓存失效策略
            try:
                super()._invalidate_cache_on_update()
            except Exception as inner_e:
                logger.error(f"降级缓存失效策略也失败: {str(inner_e)}")