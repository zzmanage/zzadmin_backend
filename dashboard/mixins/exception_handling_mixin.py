import logging
from functools import wraps
from rest_framework import status
from rest_framework.response import Response
import time
from django.conf import settings

logger = logging.getLogger(__name__)


class ExceptionHandlingMixin:
    """
    统一异常处理混入类
    提供标准化的异常处理装饰器，减少重复代码，确保异常处理的一致性
    """

    def handle_exceptions(self, default_return=None, log_level="error", re_raise=False):
        """
        异常处理装饰器，用于包装视图方法
        
        Args:
            default_return: 异常发生时的默认返回值
            log_level: 日志级别 ('debug', 'info', 'warning', 'error', 'critical')
            re_raise: 是否重新抛出异常让全局中间件处理
        
        Returns:
            function: 包装后的视图方法
        """
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 获取self实例
                self_instance = args[0] if args else None
                request = getattr(self_instance, 'request', None)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    # 记录函数执行时间（调试模式下）
                    if settings.DEBUG:
                        exec_time = (time.time() - start_time) * 1000
                        logger.debug(f"方法 {func.__name__} 执行耗时: {exec_time:.2f}ms")
                    return result
                except Exception as e:
                    # 获取更多上下文信息用于日志记录
                    context_info = {
                        'function': func.__name__
                    }
                    
                    # 尝试从参数中获取请求对象，用于记录更多上下文
                    if request:
                        context_info['user'] = request.user.id if request.user.is_authenticated else 'anonymous'
                        context_info['path'] = request.path
                        context_info['method'] = request.method
                        # 安全地记录请求参数，避免敏感信息
                        try:
                            if request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, 'data') and request.data:
                                context_info['data_sample'] = str(request.data)[:500]  # 只记录前500个字符
                            if request.GET:
                                context_info['query_params'] = str(request.GET)[:500]
                        except:
                            pass
                    
                    # 根据指定的日志级别记录异常
                    log_func = getattr(logger, log_level)
                    log_func(f"方法 {func.__name__} 执行异常: {str(e)}, 上下文: {context_info}")

                    # 记录详细的异常信息（调试模式下）
                    if settings.DEBUG:
                        logger.exception(f"方法 {func.__name__} 执行异常详情:")
                    
                    # 如果设置了重新抛出异常，让全局中间件处理
                    if re_raise:
                        raise
                    
                    # 如果default_return是Response对象并且在DEBUG模式下，添加更多错误详情
                    if isinstance(default_return, Response) and settings.DEBUG:
                        # 创建一个新的Response对象，而不是尝试深拷贝
                        debug_data = default_return.data
                        # 如果响应数据是字典类型，添加调试信息
                        if isinstance(debug_data, dict):
                            debug_data = debug_data.copy()  # 复制原始数据，避免修改
                            debug_data['debug_info'] = {
                                'error_type': type(e).__name__,
                                'error_message': str(e),
                                'function': func.__name__,
                                **context_info
                            }
                        # 创建一个新的Response对象
                        debug_response = Response(
                            debug_data,
                            status=default_return.status_code,
                            headers=default_return.headers
                        )
                        return debug_response

                    # 如果default_return是字符串，将其包装为标准的错误响应
                    if isinstance(default_return, str):
                        return Response(
                            {"status": "error", "message": default_return},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                    return default_return if default_return is not None else {
                        "status": "error", 
                        "message": "操作失败，请稍后重试"
                    }

            return wrapper

        return decorator
    
    def safe_api_call(self, func, *args, **kwargs):
        """
        安全地调用API函数，捕获并处理异常
        
        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            tuple: (success, result)，其中success是布尔值，result是函数结果或错误信息
        """
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.error(f"API调用 {func_name} 失败: {str(e)}")
            return False, str(e)

    def handle_api_exception(self, e, default_message="API请求失败"):
        """
        处理API异常，返回标准化的错误响应
        
        Args:
            e: 异常对象
            default_message: 默认错误消息
        
        Returns:
            Response: 标准化的错误响应
        """
        logger.error(f"API异常: {str(e)}")
        return Response(
            {
                "status": "error",
                "message": default_message,
                "error_details": str(e) if settings.DEBUG else None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# 全局的异常处理装饰器，便于在非类视图中使用
def api_exception_handler(default_return=None, log_level="error", re_raise=False):
    """
    全局API异常处理装饰器
    
    Args:
        default_return: 异常发生时的默认返回值
        log_level: 日志级别
        re_raise: 是否重新抛出异常
    
    Returns:
        function: 装饰器函数
    """
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # 记录函数执行时间（调试模式下）
                if settings.DEBUG:
                    exec_time = (time.time() - start_time) * 1000
                    logger.debug(f"函数 {func.__name__} 执行耗时: {exec_time:.2f}ms")
                return result
            except Exception as e:
                # 记录异常
                log_func = getattr(logger, log_level)
                log_func(f"函数 {func.__name__} 执行异常: {str(e)}")
                
                if settings.DEBUG:
                    logger.exception(f"函数 {func.__name__} 异常详情:")
                
                if re_raise:
                    raise
                
                if isinstance(default_return, Response) and settings.DEBUG:
                    debug_data = default_return.data
                    if isinstance(debug_data, dict):
                        debug_data = debug_data.copy()
                        debug_data['debug_info'] = {
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'function': func.__name__
                        }
                    return Response(
                        debug_data,
                        status=default_return.status_code,
                        headers=default_return.headers
                    )
                
                return default_return if default_return is not None else {
                    "status": "error", 
                    "message": "操作失败，请稍后重试"
                }
        
        return wrapper
    
    return decorator