"""
自定义装饰器模块
提供常用的装饰器来增强视图函数和API的功能
"""
import time
import functools
import logging
from typing import Callable, Optional, Any
from django.http import JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)


def timing_decorator(log_level: str = 'info') -> Callable:
    """
    性能计时装饰器
    记录函数执行时间并记录日志
    
    :param log_level: 日志级别 ('debug', 'info', 'warning', 'error')
    :return: 装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_time = time.perf_counter() - start_time
                log_message = f"Function {func.__name__} executed in {elapsed_time:.4f} seconds"
                
                if log_level == 'debug':
                    logger.debug(log_message)
                elif log_level == 'warning':
                    logger.warning(log_message)
                elif log_level == 'error':
                    logger.error(log_message)
                else:
                    logger.info(log_message)
        return wrapper
    return decorator


def cache_decorator(
    timeout: int = 60,
    key_prefix: str = '',
    key_func: Optional[Callable] = None
) -> Callable:
    """
    缓存装饰器
    缓存函数返回值，减少重复计算
    
    :param timeout: 缓存超时时间(秒)
    :param key_prefix: 缓存键前缀
    :param key_func: 自定义缓存键生成函数
    :return: 装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{key_prefix}{func.__name__}_{hash(f'{args}_{kwargs}')}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return decorator


def retry_decorator(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    重试装饰器
    当函数抛出指定异常时自动重试
    
    :param max_retries: 最大重试次数
    :param delay: 初始延迟时间(秒)
    :param backoff: 延迟倍数
    :param exceptions: 需要重试的异常类型
    :return: 装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{max_retries}: {str(e)}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"Function {func.__name__} failed after {max_retries} attempts")
            raise last_exception
        return wrapper
    return decorator


def validate_parameters(*required_params: str) -> Callable:
    """
    参数验证装饰器
    确保请求中包含必要的参数
    
    :param required_params: 必填参数列表
    :return: 装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs) -> Any:
            # 获取请求参数
            if request.method == 'GET':
                params = request.GET
            else:
                try:
                    params = request.data if hasattr(request, 'data') else request.POST
                except Exception:
                    params = request.POST
            
            # 检查必填参数
            missing_params = [param for param in required_params if param not in params]
            
            if missing_params:
                error_message = f"Missing required parameters: {', '.join(missing_params)}"
                logger.warning(error_message)
                return JsonResponse({
                    'code': 400,
                    'message': error_message,
                    'data': {}
                }, status=400)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def handle_exceptions(
    return_json: bool = True,
    default_message: str = 'An error occurred'
) -> Callable:
    """
    异常处理装饰器
    统一处理函数中的异常
    
    :param return_json: 是否返回JSON响应
    :param default_message: 默认错误消息
    :return: 装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Exception in {func.__name__}: {str(e)}")
                
                if return_json:
                    return JsonResponse({
                        'code': 500,
                        'message': str(e) if str(e) else default_message,
                        'data': {}
                    }, status=500)
                else:
                    raise
        return wrapper
    return decorator


def singleton(cls: type) -> type:
    """
    单例装饰器
    确保类只有一个实例
    
    :param cls: 要装饰的类
    :return: 单例类
    """
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs) -> Any:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


class classproperty(property):
    """
    类属性装饰器
    允许定义类级别的属性
    
    使用方式:
        class MyClass:
            _value = 42
            
            @classproperty
            def value(cls):
                return cls._value
    """
    def __get__(self, cls, owner):
        return self.fget(owner)
