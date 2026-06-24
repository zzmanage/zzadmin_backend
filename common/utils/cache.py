"""
缓存辅助工具模块
提供缓存装饰器和缓存管理功能
"""

import hashlib
from functools import wraps
from django.core.cache import cache
from django.conf import settings


def cache_decorator(timeout=None):
    """
    缓存装饰器
    用法:
        @cache_decorator(timeout=3600)
        def get_user_stats(user_id):
            return stats
    """
    if timeout is None:
        timeout = getattr(settings, 'CACHE_TIMEOUT', 3600)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_args = str(args) + str(kwargs)
            cache_key = f"cache:{func.__name__}:{hashlib.md5(key_args.encode()).hexdigest()}"

            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def cache_key(prefix=""):
    """生成缓存键"""
    def generate(*args, **kwargs):
        key_args = str(args) + str(kwargs)
        return f"{prefix}:{hashlib.md5(key_args.encode()).hexdigest()}" if prefix else hashlib.md5(key_args.encode()).hexdigest()
    return generate
