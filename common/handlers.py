"""
统一异常处理中间件
捕获并处理所有异常，返回统一格式的错误响应
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

from common.response import APIResponse
from common.exceptions import APIException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """自定义异常处理器"""
    # 处理自定义API异常
    if isinstance(exc, APIException):
        logger.error(f"API异常: {exc.message} (code: {exc.code})")
        return APIResponse.error(message=exc.message, code=exc.code)

    # 处理Django REST Framework的验证异常
    if isinstance(exc, DRFValidationError):
        error_detail = exc.detail
        if isinstance(error_detail, dict):
            first_field = next(iter(error_detail.keys()))
            message = error_detail[first_field][0] if error_detail[first_field] else "数据验证失败"
        elif isinstance(error_detail, list):
            message = error_detail[0] if error_detail else "数据验证失败"
        else:
            message = str(error_detail)
        logger.warning(f"数据验证失败: {message}")
        return APIResponse.error(message=message, code=400)

    # 处理Django权限异常
    if isinstance(exc, DjangoPermissionDenied):
        logger.warning("权限拒绝")
        return APIResponse.error(message="权限不足", code=403)

    # 处理其他未知异常
    logger.error(f"未知异常: {str(exc)}", exc_info=True)

    # 调用默认异常处理器
    response = exception_handler(exc, context)

    if response is not None:
        return APIResponse.error(
            message=response.data.get('detail', '操作失败'),
            code=response.status_code
        )

    return APIResponse.error(message="服务器内部错误", code=500)
