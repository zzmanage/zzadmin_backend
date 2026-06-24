"""
Common 模块 - 通用工具和基础组件
提供统一响应、异常处理、视图基类、工具函数等
"""

# 统一响应
from .response import APIResponse

# 异常类
from .exceptions import (
    APIException,
    ValidationError,
    PermissionDenied,
    NotFoundError,
    AuthenticationError,
    ServerError,
    ConflictError
)

# 视图基类
from .views import BaseViewSet, ReadOnlyViewSet, ActionViewSet

# 分页器
from .pagination import (
    CustomPageNumberPagination,
    LargeResultsSetPagination,
    SmallResultsSetPagination
)

# 异常处理器 (用于 settings.py)
from .handlers import custom_exception_handler

# 工具函数
from .utils import (
    # cache
    cache_decorator, cache_key,
    # date
    format_datetime, format_date, parse_datetime, parse_date, now, today,
    start_of_day, end_of_day, week_range, month_range, quarter_range, date_range, days_between,
    # string
    is_empty, trim, truncate, random_string, random_number,
    camel_to_snake, snake_to_camel, mask_phone, mask_email, remove_html, safe_int, safe_float
)

__all__ = [
    # response
    'APIResponse',
    # exceptions
    'APIException', 'ValidationError', 'PermissionDenied', 'NotFoundError',
    'AuthenticationError', 'ServerError', 'ConflictError',
    # views
    'BaseViewSet', 'ReadOnlyViewSet', 'ActionViewSet',
    # pagination
    'CustomPageNumberPagination', 'LargeResultsSetPagination', 'SmallResultsSetPagination',
    # handler
    'custom_exception_handler',
    # utils
    'cache_decorator', 'cache_key',
    'format_datetime', 'format_date', 'parse_datetime', 'parse_date', 'now', 'today',
    'start_of_day', 'end_of_day', 'week_range', 'month_range', 'quarter_range', 'date_range', 'days_between',
    'is_empty', 'trim', 'truncate', 'random_string', 'random_number',
    'camel_to_snake', 'snake_to_camel', 'mask_phone', 'mask_email', 'remove_html', 'safe_int', 'safe_float',
]
